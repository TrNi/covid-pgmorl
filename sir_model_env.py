import numpy as np
import matplotlib.pyplot as plt

class model_calibration(object):
    def __init__(self,O_I,ac,M = 9986857, D = 9):
      # Inputs: (Assume that all quantities are with consistent units)
      # 1. Observed cumulative confirmed cases.
      # 3. Action time series, ac (an n_t by 1 column vector)
      # 4. Total population M, a constant number (we ignore the population change due to natural born or death); M = 9986857 is Total population as per July,2019 Census data. 
      # 5. Mean time delay of a infected person be confirmed. D = 9, suggested by Sun et al. 2020, Pellis et al. 2020
      self.X_R = O_I[0:-D] # Removal population time series, X_R (an n_t by 1 column vector)
      self.X_I = O_I[D:]-O_I[0:-D] # Infected population time series, X_I (an n_t by 1 column vector)
      self.ac = ac[0:-D]
      self.M = M
      self.X_S = self.M - self.X_R - self.X_I
      self.D = D # Infected to removal delay

      # added by Andy Chen for the step class that inherits this class (change as needed)
      self.beta = 0
      self.gamma = 0

    def model_mls(self):
      # Outputs:
      # model parameters beta, gamma
      # Method: Maximum likelihood Estimation (Report section 2.2)

      # Beta
      Z_S = self.X_S[0:-1] * self.X_I[0:-1] / self.M
      Y_S = self.X_S[0:-1] - self.X_S[1:]
      ac_list = np.unique(self.ac)
      beta = [0]*len(ac_list) # a list of zeros of same length as 'ac_list'.
      # print(self.X_S[:5], self.X_I[:5], self.X_R[:5])
      # print(np.array([np.zeros(self.D,1),self.ac[0:-self.D]]))
      # print(self.ac[0:-self.D])
      # ac_shift = np.concatenate((np.zeros((self.D,1)), self.ac[0:-self.D]))
      # ac_shift = np.array([np.zeros((1,self.D)),self.ac[0:-self.D]])
      # ac_shift = np.hstack(   (np.zeros((1,self.D)),   self.ac[0:-self.D]))
      # ac_shift = np.pad(self.ac[0:-self.D], (self.D, 0), 'edge')
      # print(ac_shift)
      for index, ac in enumerate(ac_list):
          ind_ac = np.where(self.ac[0:-1] == ac) # data index
          # ind_ac = np.where(ac_shift[0:-1] == ac) # data index
          beta[index] = np.sum(Y_S[ind_ac]) / np.sum(Z_S[ind_ac]) 
      
      # Gamma
      Z_R = self.X_I[0:-1]
      Y_R = self.X_R[1:]-self.X_R[0:-1]
      gamma = np.sum(Y_R) / np.sum(Z_R)
      # print(sum(Z_R==0))

      # added by Andy Chen for the step class that inherits this class (change as needed)
      self.beta = beta
      self.gamma = gamma
      return beta, gamma

    def model_validate(self,beta,gamma):
      # Simulate data and compare
      Nsim = 1000 # Number of simulations
      T = len(self.X_R) # Horizon

      X_R_s = np.zeros((Nsim,T))
      X_I_s = np.zeros((Nsim,T))
      X_S_s = np.zeros((Nsim,T))
      ac_list = np.unique(self.ac)
      # ac_shift = np.pad(self.ac[0:-self.D], (self.D, 0), 'edge')

      for mc in range(Nsim): # Loop over all samples 

          # Initial conditions
          X_R_s[mc][0] = self.X_R[0]
          X_I_s[mc][0] = self.X_I[0]
          X_S_s[mc][0] = self.X_S[0]

          for t in range(1, T): # Loop over all time steps

              # Current beta (depends on the action of the current step)
              ind_beta = np.squeeze(np.where(ac_list == self.ac[t]))
              # ind_beta = np.squeeze(np.where(ac_list == ac_shift[t]))
              beta_t = beta[ind_beta]

              # # The GSIR model (free-run)
              # e_S = np.random.poisson(beta_t*X_S_s[mc][t-1]*X_I_s[mc][t-1]/self.M)
              # e_R = np.random.binomial(X_I_s[mc][t-1], gamma)
              # X_S_s[mc][t] = X_S_s[mc][t-1] - e_S
              # X_R_s[mc][t] = X_R_s[mc][t-1] + e_R
              # X_I_s[mc][t] = self.M - X_S_s[mc][t] - X_R_s[mc][t]
              
              # The GSIR model (One-step-ahead)
              e_S = np.random.poisson(beta_t*self.X_S[t-1]*self.X_I[t-1]/self.M)
              e_R = np.random.binomial(self.X_I[t-1], gamma)
              X_S_s[mc][t] = X_S_s[mc][t-1] - e_S
              X_R_s[mc][t] = X_R_s[mc][t-1] + e_R
              X_I_s[mc][t] = self.M - X_S_s[mc][t] - X_R_s[mc][t]
      
      t = range(T)
      print('Red: Observation, Gray: Prediction samples')
      print('Removal population (confirmed cases)')
      h1=plt.plot(t, self.X_R, color='r', linewidth=2.0)
      for mc in range(Nsim):
          h2=plt.plot(t, X_R_s[mc][:], color=[0.5, 0.5, 0.5], linewidth=0.5)
      plt.title('Removal population')
      # plt.legend((h1,h2),('Observation','Prediction'))
      plt.show()

      print('Infected population')
      plt.plot(t, self.X_I, color='r', linewidth=2.0)
      for mc in range(Nsim):
          plt.plot(t, X_I_s[mc][:], color=[0.5, 0.5, 0.5], linewidth=0.5)
      plt.title('Infected population')
      # plt.legend((h1,h2),('Observation','Prediction'))
      plt.show()

      print('Susceptible population')
      plt.plot(t, self.X_S, color='r', linewidth=2.0)
      for mc in range(Nsim):
          plt.plot(t, X_S_s[mc][:], color=[0.5, 0.5, 0.5], linewidth=0.5)
      plt.title('Susceptible population')
      # plt.legend((h1,h2),('Observation','Prediction'))
      plt.show()


class SIR_env(object):
  def __init__(self, model_calibration):
    '''
    SIR population dynamics model environment that allows user to evolve through time given action parameters.

    Input:
    - model_calibration:      SIR model calibration to be associated to this object and where hyperparameters will be drawn

    '''
    self.model_calibration = model_calibration

    self.X_S_true = np.array([self.model_calibration.X_S[0]])
    self.X_I_true = np.array([self.model_calibration.X_I[0]])
    self.X_R_true = np.array([self.model_calibration.X_R[0]])
    self.X_S = np.array([self.model_calibration.X_S[0]])
    self.X_I = np.array([self.model_calibration.X_I[0]])
    self.X_R = np.array([self.model_calibration.X_R[0]])
    self.std_X_S = np.zeros(1)
    self.std_X_I = np.zeros(1)
    self.std_X_R = np.zeros(1)

    self.beta = self.model_calibration.beta
    print(self.beta)
    self.gamma = self.model_calibration.gamma
    self.M = self.model_calibration.M

  def set_seed(self, seed):
    '''
    Defines the seed for reproducibility in the stochastic model.

    Input:
    - seed:                   random seed to use when using the step functions
    '''
    np.random.seed(seed)

  def time_step(self, action):
    '''
    Evolve the model through one time step given an action.

    Input:
    - action:                 action to use when evolving the model by one time step

    '''
    # mean population transition from X_S to X_I
    mean_e_I_new = self.beta[action]*self.X_S[-1]*self.X_I[-1]/self.M
    # mean population transition from X_I to X_R
    mean_e_R_new = self.gamma*self.X_I[-1]

    # new mean populations
    X_S_new = self.X_S_true[-1] - mean_e_I_new
    X_I_new = self.X_I_true[-1] + mean_e_I_new - mean_e_R_new
    X_R_new = self.X_R_true[-1] + mean_e_R_new

    # error propagation due to stochastic model
    std_X_S_new = np.sqrt(self.beta[action]*self.X_S_true[-1]*self.X_I_true[-1]/self.M)
    std_X_R_new = self.X_I_true[-1] * (self.gamma)*(1-self.gamma)
    std_X_I_new = np.sqrt(std_X_S_new**2 + std_X_R_new**2)

    # update X lists and std lists
    self.X_S_true = np.append(self.X_S, X_S_new)
    self.X_I_true = np.append(self.X_I, X_I_new)
    self.X_R_true = np.append(self.X_R, X_R_new)

    self.std_X_S = np.append(self.std_X_S, np.sqrt(self.std_X_S[-1]**2 + std_X_S_new**2))
    self.std_X_I = np.append(self.std_X_I, np.sqrt(self.std_X_I[-1]**2 + std_X_I_new**2))
    self.std_X_R = np.append(self.std_X_R, np.sqrt(self.std_X_R[-1]**2 + std_X_R_new**2))

  def get_deterministic(self):
    '''
    Retrieve the most recently calculated X_S, X_I, and X_R mean values (as if the model was deterministic).

    Output:
    - X_S_true:               the most recently calculated X_S
    - X_I_true:               the most recently calculated X_I
    - X_R_true:               the most recently calculated X_R

    '''
    return self.X_S_true[-1], self.X_I_true[-1], self.X_R_true[-1]

  def get_error(self):
    '''
    Retrieve the most recently calculated X_S, X_I, and X_R standard deviations (using the random variable distributions of the stochastic model).

    Output:
    - std_X_S:                the most recently calculated std_X_S
    - std_X_I:                the most recently calculated std_X_I
    - std_X_R:                the most recently calculated std_X_R

    '''
    return self.std_X_S[-1], self.std_X_I[-1], self.std_X_R[-1]

  def sample_stochastic(self):
    '''
    Samples a set of the most recently calculated X_S, X_I, and X_R values (assuming CLT).

    Output:
    - X_S_samp:               the most recently calculated X_S
    - X_I_samp:               the most recently calculated X_I
    - X_R_samp:               the most recently calculated X_R

    '''
    X_S_samp = np.random.normal(self.X_S_true[-1],self.std_X_S[-1])
    X_R_samp = np.random.normal(self.X_R_true[-1],self.std_X_R[-1])
    X_I_samp = self.M - X_S_samp - X_R_samp
    return X_S_samp, X_I_samp, X_R_samp

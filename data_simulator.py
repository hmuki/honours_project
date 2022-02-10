# Simulate data from a known GPFA process

from Seq_Data_Class import Model_Specs, Trial_Class, Param_Class
import numpy as np
import scipy


def rand_params_generator(x_dim, y_dim, kernel):

    if kernel == 'rbf':
        param_eps = 1e-3 * np.ones((x_dim,))
        param_gamma = np.random.uniform(0, 1, x_dim).tolist()
        Q = 0

    elif kernel == 'sm':
        param_gamma = []
        for i in range(x_dim):
            weights = np.random.uniform(0, 1, 3).tolist()
            weights = weights / np.sum(weights)
            weights = weights.tolist()
            mu = np.random.uniform(0, 1, Q).tolist()
            vs = np.random.uniform(0, 1, Q).tolist()
            param_gamma.append(weights + mu + vs)
            Q = 3
    param_C = np.random.normal(loc=0.0, scale=1.0, size=(y_dim, x_dim))
    param_R = np.abs(np.random.normal(0, 1, y_dim))
    param_d = np.random.normal(loc=0.0, scale=1.0, size=(y_dim,))
    return Param_Class(kernel, param_gamma=param_gamma, param_eps=param_eps, param_d=param_d, param_C=param_C, param_R=param_R, param_q=Q)


def sample_data(kernel, params, num_trials, trial_length):
    #kernel: RBF or SM
    # params: type params_class()
    # time: how many independent trail class
    # create a seq of tria_class
    seq = [Trial_Class(i, 20, 1, None, None) for i in range(num_trials)]
    # Load parameters
    R = params.R
    d = params.d
    C = params.C
    sigma_n = params.eps
    T = trial_length
    q = C.shape[0]
    p = C.shape[1]

    # create kernel K
    if kernel == 'rbf':
        K = []
        Tdif = np.tile(np.arange(1, T+1).reshape((T, 1)), (1, T)) - np.tile(np.arange(1, T+1), (T, 1))
        diffSq = Tdif ** 2
        for i in range(p):
            const = params.eps[1]
            p = params.gamma[1]
            temp = (1-const) * np.exp(-p / 2 * diffSq)
            Kmax = temp + const * np.identity(diffSq.shape[0])
            K.append(Kmax)

    if kernel == 'sm':
        K = []
        Tdif = np.tile(np.arange(1, T+1).reshape((T, 1)), (1, T)) - np.tile(np.arange(1, T+1), (T, 1))
        diffSq = Tdif ** 2
        for i in range(p):
            w = params.gamma[i][:params.Q]
            m = params.gamma[i][params.Q:params.Q*2]
            v = params.gamma[i][params.Q*2:params.Q*3]
            Km = np.zeros(diffSq.shape)
            for j in range(len(w)):
                Km = Km + w[j] * np.exp(-2 * np.pi**2 * v[j] **
                                        2 * diffSq) * np.cos(2 * np.pi * Tdif.T * m[j])
            K.append(Km)

    # sampling once
    def sample_once():
        X = []
        for i in range(len(K)):
            X.append(np.random.multivariate_normal(np.zeros(T), K[i], 1)[0])
        X = np.array(X)

        Y = []
        for i in range(len(X.T)):
            Y.append(np.random.multivariate_normal((np.dot(C, X.T[i])+d), R))
        Y = np.array(Y).T
        return X, Y

    # adding X,Y to trial in the seq
    for i in range(num_trials):
        seq[i].x, seq[i].y = sample_once()
    return seq, params


def generate_trial_data(params, K, xDim, T):
    X = np.zeros((xDim, T))
    for i in range(xDim):
        X[i, :] = np.random.multivariate_normal(np.zeros(T), K[i])
    Y = np.zeros((params.C.shape[0], T))
    for i in range(T):
        Y[:, i] = np.random.multivariate_normal(
            np.matmul(params.C, X[:, i]) + params.d, params.R)
    return Y


# Save to file
def save_data(filepath, sample_data, params):
    # sample_data is a seq of trial
    # save X,Y to mat file
    save = {'seq': [[]]}
    for i in range(len(sample_data)):
        save['seq'][0].append([[[sample_data[i].trial_id]], [[sample_data[i].T]], [
                              [sample_data[i].seq_id]], sample_data[i].x, sample_data[i].y])
    save['currentParams'] = [[[[params.cov_type], [params.gamma], [
        params.eps], params.d[:, np.newaxis], params.C, params.R]]]
    # save['extra_opts'] = [['kernSDList']],[[30]]]
    scipy.io.savemat(filepath, save, do_compression=True)
    print("Saved file at", filepath)


def save_params(filepath, params):
    save = {}
    save['currentParams'] = [[[[params.cov_type], [params.gamma], [
        params.eps], params.d[:, np.newaxis], params.C, params.R]]]
    scipy.io.savemat(filepath, save, do_compression=True)
    print("Saved file at", filepath)


# Load from file
def load_data(filepath):
    model_data = Model_Specs()
    model_data.data_from_mat(filepath)
    data = model_data.get_data()
    return data


# Load from dataset
def load_real_world_data(filepath, movie=False, natural_or_gratings=False, shifted_natural=False):
    model_data = Model_Specs()
    if movie:
        model_data.data_from_movie(filepath)
    data = model_data.get_data()
    return data


# Load parameters from mat file
def load_params(filepath):
    params = Param_Class()
    params.params_from_mat(filepath)
    return params


if __name__ == "__main__":
    print("Simulating data")
    cov_type = 'sm'  # rbf or 'sm'
    params = load_params('input/example_params_{}.mat'.format(cov_type))
    sampled_data, saved_params = sample_data(cov_type, params, 56, 20)
    print('Shape of x is ', sampled_data[0].x.shape)
    print('Shape of y is ', sampled_data[0].y.shape)
    save_data('input/fake_data_{}.mat'.format(cov_type),
              sampled_data, saved_params)

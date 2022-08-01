# Functional-GEL
Implementation of Functional Generalized Empirical Likelihood Estimators 
for conditional moment restriction problems and code to reproduce the experiments in the corresponding 
[paper](https://proceedings.mlr.press/v162/kremer22a.html).

Parts of the implementation are based on the codebase for the [Variational Method of Moments](https://github.com/CausalML/VMM) estimator.

## Installation
To install the package, create a virtual environment and run the setup file from within the folder containing this README, e.g. using the following commands:
```bash
python3 -m venv fgel-venv
source fgel-venv/bin/activate
pip install -e .
```

## Using FGEL
FGEL estimators can be trained following the below syntax. The code can also be found in the notebook [example.ipynb](https://github.com/HeinerKremer/Functional-GEL/blob/main/example.ipynb).
```python
import torch
import numpy as np
from fgel.estimation import fgel_estimation


# Generate some data
def generate_data(n_sample):
    e = np.random.normal(loc=0, scale=1.0, size=[n_sample, 1])
    gamma = np.random.normal(loc=0, scale=0.1, size=[n_sample, 1])
    delta = np.random.normal(loc=0, scale=0.1, size=[n_sample, 1])

    z = np.random.uniform(low=-3, high=3, size=[n_sample, 1])
    t = np.reshape(z[:, 0], [-1, 1]) + e + gamma
    y = np.abs(t) + e + delta
    return {'t': t, 'y': y, 'z': z}

train_data = generate_data(n_sample=100)
validation_data = generate_data(n_sample=100)
test_data = generate_data(n_sample=10000)


# Define a PyTorch model $f$ and a moment function $\psi$
model = torch.nn.Sequential(
            torch.nn.Linear(1, 20),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(20, 3),
            torch.nn.LeakyReLU(),
            torch.nn.Linear(3, 1)
        )

def moment_function(model_evaluation, y):
    return model_evaluation - y

# Train the model using Kernel/Neural-FGEL
trained_model, stats = fgel_estimation(model=model,                     # Use any PyTorch model
                                       train_data=train_data,           # Format {'t': t, 'y': y, 'z': z}
                                       moment_function=moment_function, # moment_function(model_eval, y) -> (n_sample, dim_y)
                                       version='kernel',                # 'kernel' or 'neural' FGEL version
                                       divergence=None,                 # If 'None' optimize as hyperparam, otherwise choose from ['chi2', 'kl', 'log']
                                       reg_param=None,                  # If 'None' optimize as hyperparam
                                       validation_data=validation_data, # Format {'t': t, 'y': y, 'z': z}
                                       val_loss_func=None,              # Custom validation loss: val_loss_func(model, validation_data) -> float
                                       verbose=True)

# Make prediction
y_pred = trained_model(test_data['t'])
```


[comment]: <> (## Reproducibility)

[comment]: <> (The experimental results presented in the [paper]&#40;https://proceedings.mlr.press/v162/kremer22a.html&#41; can be reproduced by running the script [run_experiment.py]&#40;run_experiment.py&#41; via)

[comment]: <> (```)

[comment]: <> (python3 run_experiment.py --experiment exp --run_all --method method --rollouts 50)

[comment]: <> (```)

[comment]: <> (with `exp in ['heteroskedastic', 'network_iv']` and `methods in []`.)

## Citation
If you use parts of the code in this repository for your own research purposes, please consider citing:
```
@InProceedings{pmlr-v162-kremer22a,
  title = 	 {Functional Generalized Empirical Likelihood Estimation for Conditional Moment Restrictions},
  author =       {Kremer, Heiner and Zhu, Jia-Jie and Muandet, Krikamol and Sch{\"o}lkopf, Bernhard},
  booktitle = 	 {Proceedings of the 39th International Conference on Machine Learning},
  pages = 	 {11665--11682},
  year = 	 {2022},
  editor = 	 {Chaudhuri, Kamalika and Jegelka, Stefanie and Song, Le and Szepesvari, Csaba and Niu, Gang and Sabato, Sivan},
  volume = 	 {162},
  series = 	 {Proceedings of Machine Learning Research},
  month = 	 {17--23 Jul},
  publisher =    {PMLR},
  pdf = 	 {https://proceedings.mlr.press/v162/kremer22a/kremer22a.pdf},
  url = 	 {https://proceedings.mlr.press/v162/kremer22a.html},
}
```

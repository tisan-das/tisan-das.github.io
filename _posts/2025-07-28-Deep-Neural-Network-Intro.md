---
layout: post
title: Introduction to Deep Learning - Deep Neural Network
image: /images/deep-learning/01_01_ai_vs_ml_vs_deep_learning.png
series: "Deep Learning Fundamentals"
categories: ["Deep Learning", "Fundamentals"]
tags: [neural-networks, deep-learning]
math: true
published: true
---
The progress of the deep learning field over the last couple of years is astounding. From creating vague images in 2015 to generating realistic videos with just a few minutes of prompts, the changes are truly remarkable. 

{% include series-nav.html %}

![AI vs ML vs deep learning](/images/deep-learning/01_01_ai_vs_ml_vs_deep_learning.png){: .w-75 .light }
![AI vs ML vs deep learning](/images/deep-learning/01_01_ai_vs_ml_vs_deep_learning-dark.png){: .w-75 .dark }
_AI vs ML vs deep learning_

Deep learning aims to extract features from the data. Engineering the features manually is time-consuming, error-prone, and unscalable. Hence, neural networks are used to extract different levels of features in a lower-dimensional scenario.

### Perceptron
![Perceptron](/images/deep-learning/01_02_perceptron.png){: .light }
![Perceptron](/images/deep-learning/01_02_perceptron-dark.png){: .dark }
_Perceptron_

A single unit of a neuron in a neural network is referred to as a perceptron. The purpose of the activation function is to introduce non-linearity in the network. This non-linearity enables the network to learn complex models with ease, which would otherwise require a larger network.

![Perceptron: deep neural nw](/images/deep-learning/01_03_deep_neural_nw.png){: .w-75 .light }
![Perceptron: deep neural nw](/images/deep-learning/01_03_deep_neural_nw-dark.png){: .w-75 .dark }
_Perceptron: deep neural nw_

### Loss & Gradients

The loss of our network measures the cost of incorrect predictions. Empirical loss measures the total loss across the dataset.

**Mean-squared error** (continuous targets):

$$
\mathcal{L}_{\mathrm{MSE}} = \frac{1}{N}\sum_{i=1}^{N}\bigl(y_i - \hat{y}_i\bigr)^2
$$

**Binary cross-entropy** (models that output a probability $\hat{y}\in(0,1)$):

$$
\mathcal{L}_{\mathrm{CE}} = -\frac{1}{N}\sum_{i=1}^{N}\Bigl[y_i\log\hat{y}_i + (1-y_i)\log(1-\hat{y}_i)\Bigr]
$$

We aim to determine network weights that yield the lowest loss. **Gradient descent** converges to a local minimum iteratively by stepping against the gradient:

$$
w \leftarrow w - \eta\,\nabla_w\mathcal{L}(w)
$$

where $\eta$ is the learning rate and $\nabla_w\mathcal{L}$ is the gradient of the loss w.r.t. the weights.

![Loss & Gradients: gradient descent](/images/deep-learning/01_04_gradient_descent.png){: .w-75 .light }
![Loss & Gradients: gradient descent](/images/deep-learning/01_04_gradient_descent-dark.png){: .w-75 .dark }
_Loss & Gradients: gradient descent_

The way the gradients are calculated in a step-by-step manner from output to input direction is called backpropagation. It's worth noting that the gradient descent algorithm is inherently a greedy approach.

Use an adaptive learning rate $\eta$ to overcome the overshooting and undershooting problems commonly associated with fixed learning rates. Different gradient descent algorithms are proposed based upon different adaptive mechanisms. SGD and Adam are the most widely used variations of gradient descent.

Gradient calculation is expensive. Hence, it is generally computed over a batch.

Additionally, if the training data is small, there's a possibility of model overfitting, where the network memorizes the training data rather than understanding the underlying features, which can increase the validation loss, even though the training loss is minimal. This can be discouraged in different ways. Regularization is one such mechanism; it simply nudges the network to use a simple model.
1. During training, randomly set some activations to 0 with some probability. It prevents the network from depending on any specific node.
2. Early stopping: Stop training before we can have a chance of overfitting

![Loss & Gradients: early stopping](/images/deep-learning/01_05_early_stopping.png){: .light }
![Loss & Gradients: early stopping](/images/deep-learning/01_05_early_stopping-dark.png){: .dark }
_Loss & Gradients: early stopping_

### Concepts covered

![Concepts covered: overview](/images/deep-learning/01_06_overview.png){: .light }
![Concepts covered: overview](/images/deep-learning/01_06_overview-dark.png){: .dark }
_Concepts covered: overview_

### References:
1. [MIT Introduction to Deep Learning 6.S191](https://www.youtube.com/watch?v=alfdI7S6wCY&list=PLtBw6njQRU-rwp5__7C0oIVt26ZgjG9NI&index=1)

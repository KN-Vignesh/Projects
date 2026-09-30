# CNN Fundamentals & Image Preprocessing

Deep learning image preprocessing and Convolutional Neural Network (CNN) architecture construction using TensorFlow and Keras on the MNIST handwritten digit dataset.

## Overview

This notebook provides a step-by-step tutorial on preparing raw image tensors for deep learning. Using the MNIST dataset, it details the foundational transformations required before feeding visual data into convolutional networks: 4D tensor reshaping, float normalization (0–255 to 0.0–1.0), and categorical one-hot label encoding, culminating in a compiled `Sequential` Keras CNN model.

## Key Steps Demonstrated

1. **4D Tensor Reshaping:** Converting 2D grayscale arrays `(samples, 28, 28)` into the 4D input shape expected by convolutional layers: `(samples, height, width, channels)`.
2. **Pixel Value Normalization:** Scaling uint8 pixel intensities from $[0, 255]$ to $[0.0, 1.0]$ float32 to stabilize gradient descent and avoid exploding gradients.
3. **One-Hot Categorical Encoding:** Transforming integer scalar class labels ($0 \dots 9$) into 10-dimensional probability vectors for categorical cross-entropy optimization.
4. **CNN Architecture Construction:** Constructing a sequential model with `Conv2D`, `MaxPooling2D`, `Flatten`, and `Dense` layers with Softmax output activation.

## Technology Stack

- **Framework:** TensorFlow / Keras
- **Libraries:** NumPy, Matplotlib

## Setup & Execution

### Prerequisites
```bash
pip install tensorflow numpy matplotlib
```

### Running the Notebook
```bash
jupyter notebook Ai-Cookbook/CNN-Fundamentals/CNN_Fundamental_Preprocessing.ipynb
```

## License
MIT License. Developed by Vignesh K N.

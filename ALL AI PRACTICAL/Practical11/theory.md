Machine Learning: Linear Regression Theory
1. Introduction to Machine Learning
Machine Learning (ML) is a subset of Artificial Intelligence that enables systems to learn patterns from data and make predictions or decisions without being explicitly programmed.
Supervised Learning
Supervised learning is a type of Machine Learning where the model is trained using labeled data. It includes:
Regression: Predicting continuous numerical values (e.g., house prices).
Classification: Predicting categorical labels (e.g., Spam or Not Spam).

3. Linear Regression
Linear Regression is one of the simplest and most widely used algorithms for predictive modeling. It establishes a linear relationship between input variables (
) and an output variable (
).
The Mathematical Model
The relationship is defined by the equation:

Where:
: Dependent variable (Target)
: Independent variable (Feature)
: Intercept (Value of when )
: Slope / Coefficient (Change in for a unit change in )
Types of Linear Regression
Simple Linear Regression: Involves only one independent variable.
Multiple Linear Regression: Involves more than one independent variable.

3. Implementation Details
Working Mechanism
Collect Dataset: Gather historical data points.
Plot Data Points: Visualize the distribution of data.
Fit a Best-fit Line: Calculate the line that best represents the trend.
Minimize Error: Use the Least Squares Method to reduce the distance between actual points and the line.
Predict: Use the resulting equation to estimate new values.
Error Metrics
To evaluate how well the model performs, we use:
MAE: Mean Absolute Error
MSE: Mean Squared Error
RMSE: Root Mean Squared Error
Feature	Description
Advantages	Simple to implement, highly interpretable, and efficient for linear trends.
Limitations	Sensitive to outliers, assumes a strictly linear relationship, and fails on complex patterns.

4. Lab Algorithm
Follow these steps to implement Linear Regression in Python:
Import required libraries (e.g., scikit-learn, pandas, matplotlib).
Load the dataset.
Split the dataset into Training and Testing sets.
Create the Linear Regression model instance.
Train the model using the training data (model.fit()).
Predict output using the test data (model.predict()).
Evaluate the model using error metrics (MAE, MSE).
Visualize the results using a scatter plot and the regression line

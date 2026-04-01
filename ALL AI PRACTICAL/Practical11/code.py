import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# Step 1: Take dataset input from user
n = int(input("Enter number of data points: "))

hours = []
marks = []

for i in range(n):
    h = float(input(f"Enter study hours for student {i+1}: "))
    m = float(input(f"Enter marks for student {i+1}: "))
    hours.append(h)
    marks.append(m)

# Step 2: Create DataFrame
df = pd.DataFrame({
    'Hours': hours,
    'Marks': marks
})

# Step 3: Define X and y
X = df[['Hours']]
y = df['Marks']

# Step 4: Train model
model = LinearRegression()
model.fit(X, y)

# Step 5: Predict using user input
new_hours = float(input("Enter study hours to predict marks: "))
prediction = model.predict([[new_hours]])

print("\nSlope (m):", model.coef_[0])
print("Intercept (b):", model.intercept_)
print(f"Predicted Marks for {new_hours} hours:", prediction[0])

# Step 6: Plot graph
predicted = model.predict(X)

plt.scatter(X, y, label="Actual Data")
plt.plot(X, predicted, label="Regression Line")
plt.xlabel("Study Hours")
plt.ylabel("Marks")
plt.title("Linear Regression with User Input")
plt.legend()
plt.show()

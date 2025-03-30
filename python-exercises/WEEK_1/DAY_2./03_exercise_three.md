# Write a program that asks the user for their age and tells them if they are allowed to vote (18 or older).
---
```python

print("\nAre you eligible to vote?")  # Show a question before asking the age

age_user = int(input("Enter your age: "))  # Ask for the user's age and convert it to integer

if age_user >= 18:  # Check if the user is 18 or older
    print("Congratulations! You are eligible to vote.")  # Message if condition is true
else:
    print("Sorry, you are not eligible to vote.")  # Message if age is less than 18


# exercise 5: secure_password.py
Write a program that compares a password entered by the user with a stored one.
If they match, print “Access granted”; otherwise, print “Access denied”.

```python
print("\nUser Access")  # Display initial access message

user_password = input("Create a password: ")  # Ask the user to create a password
print("Password saved successfully!")  # Confirm that password is stored

entered_password = input("Enter your password: ")  # Ask the user to enter the password for verification

if entered_password == user_password:  # Compare stored password with entered one
    print("Access granted!")  # If they match, access is granted
else:
    print("Access denied!")  # If they don't match, access is denied

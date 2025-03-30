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
```
If you want your password to be hidden while typing, you can use the built-in Python module `getpass`.
This allows the user to type a password without showing it on the screen — ideal for sensitive data.
This is optional. You don’t need to use it yet, but if you want to test it, here’s how.
Later on, I’ll explain how modules and libraries work in Python.

## Version using getpass:
```python
import getpass  # Module to hide password input

print("\nUser Access")

user_password = getpass.getpass("Create a password: ")  # Input hidden
print("Password saved successfully!")

entered_password = getpass.getpass("Enter your password: ")  # Hidden again

if entered_password == user_password:
    print("Access granted!")
else:
    print("Access denied!")
```

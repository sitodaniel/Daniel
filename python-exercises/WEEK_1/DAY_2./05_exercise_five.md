# exercise 5: secure_password.py
Write a program that compares a password entered by the user with a stored one.
If they match, print “Access granted”; otherwise, print “Access denied”.

```python
print("\nAcceso Usuario")
contraseña_usuario = input("Ingresa una contraseña")
print("Contraseña guardada con exito!")
acceso_usuario = input("Ingresa tu contraseña")

if acceso_usuario == contraseña_usuario:
    print("Acceso concedido!")
else:
    print("Acceso denegado!")

# 💻 Daniel's Code Notebook

Welcome to my practice repo!

## 🐍 Python Example

## If / elif / else
exercise 1
### mayor_de_dos.py
haz un programa que pida dos numero y diga cual es el mayor

```python
numero_uno = int(input("Ingresa el primer numero: "))
numero_dos = int(input("ingresa el segundo numero: "))

if numero_uno > numero_dos:
  print(f"el numero mayor es: {numero_uno}")
elif numero_dos > numero_uno:
  print(f"el numero mayor es: {numero_dos}")
else:
  print("ambos numeros son iguales")
```
## explicacion del ejercicio 
input() es una funcion de python que le pide al usuario que escriba algo por el teclado
funcionamiento paso a paso de la funcion input:
input() siempre guarda lo que escribe el usuario en cadena de texto o strings, dentro de los parentesis va entre comillas por ejemplo
```python
dato = input("¿como te llamas?: ") # recuerda que despues de input va parentesis y el texto entre comillas
```
aunque escribas "123" saldra de forma de cadena de texto para cambiar eso usas int o float
```python
numero = int(input("Escribe un número: "))
numero = float(input("Escribe un número: "))
```
### if / elif / else
if significa una condicion , se tiene que cumplir la funcion es como decir al programa que si se cumple una cosa haz esto...
elif siginifica lo mismo que if pero se usa cuando no se sumple la funcion if para a la otra funcion que seria elif
else es la misma condicion pero se usa como respaldo si no se cumple las funciones if y elif 
```python
edad = 10
if edad >= 18:
  print("Eres mayor de edad")
elif edad >= 13:
  print("Eres adolescente")
else:
  print("Eres un niño")
```

### Operadores de comparación en Python

Los operadores de comparación se utilizan para comparar valores y devuelven un resultado booleano: `True` o `False`.  
Son esenciales para tomar decisiones con estructuras como `if`, `elif` y `else`.

| Operador | Significado           | Ejemplo   | Resultado |
|----------|------------------------|-----------|-----------|
| `==`     | Igual a                | `5 == 5`  | `True`    |
| `!=`     | Distinto de            | `5 != 3`  | `True`    |
| `>`      | Mayor que              | `7 > 3`   | `True`    |
| `<`      | Menor que              | `2 < 1`   | `False`   |
| `>=`     | Mayor o igual que      | `5 >= 5`  | `True`    |
| `<=`     | Menor o igual que      | `4 <= 3`  | `False`   |

#!/bin/bash

# Verificar si el directorio "static" existe
if [ ! -d "static" ]; then
    echo "Creando el directorio 'static'..."
    mkdir static
fi

# Verificar si el archivo "styles.css" existe en "static"
if [ ! -f "static/styles.css" ]; then
    echo "Creando el archivo 'styles.css' en 'static'..."
    cat <<EOL > static/styles.css
/* Estilos básicos */
button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 10px 15px;
    cursor: pointer;
    border-radius: 5px;
}

button:hover {
    background-color: #0056b3;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}

table th, table td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}

table th {
    background-color: #f2f2f2;
    color: #333;
}
EOL
    echo "Archivo 'styles.css' creado."
fi

# Verificar si el directorio "templates" existe
if [ ! -d "templates" ]; then
    echo "Creando el directorio 'templates'..."
    mkdir templates
fi

# Verificar si el archivo "base.html" existe en "templates"
if [ ! -f "templates/base.html" ]; then
    echo "Creando el archivo 'base.html' en 'templates'..."
    cat <<EOL > templates/base.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="/static/styles.css">
    <title>{% block title %}Bodega Internacional{% endblock %}</title>
</head>
<body>
    <header>
        <h1>Bodega Internacional</h1>
    </header>
    <main>
        {% block content %}{% endblock %}
    </main>
    <footer>
        <p>&copy; 2025 Bodega Internacional</p>
    </footer>
</body>
</html>
EOL
    echo "Archivo 'base.html' creado."
fi

# Verificar permisos de los directorios y archivos
echo "Asegurando permisos adecuados..."
chmod -R 755 static templates
chmod 644 static/styles.css templates/base.html

echo "Configuración completada. El proyecto está listo para ejecutarse."
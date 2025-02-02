# DomoSapiens

Este código crea una página web simple con:

1. Un chatbot para acceder a modelos locales con ollama
2. Una base de datos de prompts prefabricados
3. Un RAG local con acceso a la carpeta de documentos que elija el usuario
3. Lo que vaya llegando

Para usarlo, necesitarás:

1. Tener ollama corriendo (asegúrate de que está configurada correctamente).
2. Haber bajado algunos modelos locales
3. Asegurarte de que tu servidor local permita CORS si estás trabajando en diferentes puertos.
4. Lanzar el servidor: `nohup python3 server.py > "logs/server_$(date +%Y%m%d_%H%M%S).log" 2>&1 &`
5. Para detener el servidor:
   ```bash
   # Encontrar el PID del proceso
   ps aux | grep "server.py"
   # Detener el proceso usando el PID encontrado
   kill <PID>
   ```

Para acceder ve a http://localhost:8800 en tu navegador.
¡A disfrutar! 😊

>>> Quiero hacer una página web sencilla para interaccionar con mi API local de deepseek mediante un chat

### Acceder a la API de DeepSeek-R1
La API de Ollama se expone por defecto en el puerto `11434`. Puedes hacer peticiones HTTP directamente 
a esta dirección.

```bash
curl -X POST "http://localhost:11434/api/generate" \
     -H "Content-Type: application/json" \
     -d '{"model": "deepseek-r1:14b", "prompt": "Hola, soy DeepSeek-R1"}'
```


### Backend - server.py

####Optimizando el Código Original

1. **Imports y Dependencias**: El código importa `yaml`, pero no se especifica un módulo concreto de YAML (por ejemplo, PyYAML). Esto puede llevar a errores si la 
dependencia `PyYAML` no está instalada.

2. **Manejo de Archivos**: No hay verificación explícita para asegurar que el contenido leído desde los archivos realmente sigue un formato esperado (por ejemplo, 
YAML delimitado por '---').

3. **Encapsulación y Escritura JSON en `list_prompts`**: La lógica de manejo de respuesta HTTP debería estar encapsulada en la función que responde al cliente, no 
dentro de `list_prompts`. Esto mantiene las responsabilidades separadas.

4. **Gestión de Excepciones**: El código captura excepciones genéricas pero podría ser más específico acerca del tipo de errores que puede manejar, y proporcionar 
mensajes de error más claros o registro de errores.

5. **Uso de Variables Globales para el Puerto**: Es mejor pasar configuraciones como el puerto a través de argumentos de línea de comandos en lugar de usar variables 
globales fijas, permitiendo flexibilidad al ejecutar el script.

6. **Configuración del Servidor**: El código no proporciona una forma de detener el servidor de manera limpia (por ejemplo, capturar señales como `SIGINT`).

7. **Mensajes de Error y Depuración**: Los mensajes de error se imprimen a la consola sin más detalles que podrían ayudar en depuración.

8. **Falta de Comentarios o Documentación Adicional**: El código podría beneficiarse de comentarios adicionales para explicar partes complejas o lógica no inmediatamente obvia.

#### Explicación de las Correcciones

- **Dependencias**: Asegúrate de que `PyYAML` está instalado (`pip install PyYAML`) para usar el módulo `yaml`.
  
- **Manejo Específico de Excepciones**: Se añadió un manejo específico de excepción para errores en la carga de YAML, separando lógicamente los posibles problemas.

- **Separación de Responsabilidades**: El proceso de respuesta HTTP se encapsula correctamente dentro del método `do_GET`.

- **Configuración Flexible**: La configuración del puerto se puede pasar como argumento al ejecutar el script (`python script.py 9000`), lo cual es más flexible que 
usar una variable global fija.

- **Manejo Limpio de Interrupciones**: Se implementó un manejo de señales para permitir detener el servidor con `Ctrl+C`.

- **Más Información en Logs**: Los mensajes de error ahora indican qué archivo causó el problema, facilitando la depuración.

Esta versión del código es más robusta y flexible, haciendo que sea más fácil de mantener e integrar en diferentes entornos.

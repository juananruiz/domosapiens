from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys
from functools import partial
import json
import os
import yaml
from datetime import datetime
import re
import signal

def format_date(date_str):
    """Convierte una fecha string a formato ISO o devuelve None si es inválida"""
    if not date_str:
        return None
    if isinstance(date_str, datetime):
        return date_str.isoformat()
    try:
        return datetime.fromisoformat(str(date_str)).isoformat()
    except (ValueError, TypeError):
        return None

class PromptHandler(SimpleHTTPRequestHandler):
    def add_cors_headers(self):
        """Añade las cabeceras CORS necesarias"""
        self.send_header('Access-Control-Allow-Origin', 'http://localhost')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE, PUT')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_POST(self):
        if self.path == '/create-prompt':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                # Validar datos requeridos
                if not data.get('title') or not data.get('content'):
                    self.send_error(400, 'Título y contenido son requeridos')
                    return

                # Crear nuevo prompt
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{timestamp}.md"
                filepath = os.path.join(os.getcwd(), 'prompts', filename)

                # Preparar contenido del archivo
                prompt_content = {
                    'title': data['title'],
                    'tags': data.get('tags', []),
                    'uses': 0,
                    'created': datetime.now().isoformat(),
                    'modified': datetime.now().isoformat()
                }

                # Escribir archivo
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('---\n')
                    yaml.dump(prompt_content, f, allow_unicode=True, sort_keys=False)
                    f.write('---\n')
                    f.write(data['content'])

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'id': timestamp}).encode())

            except Exception as e:
                print(f"Error creating prompt: {str(e)}")
                self.send_error(500, f"Error interno del servidor: {str(e)}")
        else:
            self.send_error(404)

    def do_DELETE(self):
        """Maneja las peticiones DELETE para borrar prompts"""
        base_path = self.path.split('?')[0]
        
        if base_path.startswith('/delete-prompt/'):
            try:
                prompt_id = base_path.split('/delete-prompt/')[1]
                prompt_file = os.path.join(os.getcwd(), 'prompts', f"{prompt_id}.md")
                
                if not os.path.exists(prompt_file):
                    self.send_error(404, "Prompt no encontrado")
                    return
                    
                os.remove(prompt_file)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
            except Exception as e:
                print(f"Error deleting prompt: {str(e)}")
                self.send_error(500, f"Error interno del servidor: {str(e)}")
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        """Maneja las peticiones OPTIONS para CORS preflight"""
        self.send_response(200)
        self.add_cors_headers()
        self.end_headers()

    def end_headers(self):
        """Añade headers CORS a todas las respuestas"""
        self.add_cors_headers()
        SimpleHTTPRequestHandler.end_headers(self)

    def do_GET(self):
        # Extraer la ruta base sin parámetros de consulta
        base_path = self.path.split('?')[0]
        
        if base_path == '/list-prompts':
            try:
                prompts = self.list_prompts()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = json.dumps(prompts, ensure_ascii=False)
                self.wfile.write(response.encode('utf-8'))
            except Exception as e:
                print(f"Error processing request: {str(e)}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = json.dumps({
                    'error': True,
                    'message': str(e)
                })
                self.wfile.write(error_response.encode('utf-8'))
        elif base_path.startswith('/get-prompt/'):
            try:
                prompt_id = base_path.split('/get-prompt/')[1]
                prompt_file = os.path.join(os.getcwd(), 'prompts', f"{prompt_id}.md")
                
                if not os.path.exists(prompt_file):
                    self.send_error(404, "Prompt no encontrado")
                    return
                
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
                    if match:
                        metadata = yaml.safe_load(match.group(1))
                        prompt_content = match.group(2).strip()
                        response_data = {
                            'id': prompt_id,
                            'title': metadata.get('title', ''),
                            'tags': metadata.get('tags', []),
                            'content': prompt_content
                        }
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    else:
                        self.send_error(500, "Formato de archivo inválido")
            except Exception as e:
                print(f"Error getting prompt: {str(e)}")
                self.send_error(500, f"Error interno del servidor: {str(e)}")
        else:
            # Para archivos estáticos (HTML, CSS, etc.)
            super().do_GET()

    def do_PUT(self):
        """Maneja las peticiones PUT para actualizar prompts"""
        base_path = self.path.split('?')[0]
        
        if base_path.startswith('/update-prompt/'):
            try:
                prompt_id = base_path.split('/update-prompt/')[1]
                prompt_file = os.path.join(os.getcwd(), 'prompts', f"{prompt_id}.md")
                
                if not os.path.exists(prompt_file):
                    self.send_error(404, "Prompt no encontrado")
                    return
                
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # Validar datos requeridos
                if not data.get('title') or not data.get('content'):
                    self.send_error(400, 'Título y contenido son requeridos')
                    return
                
                # Preparar contenido actualizado
                prompt_content = {
                    'title': data['title'],
                    'tags': data.get('tags', []),
                    'uses': data.get('uses', 0),
                    'created': data.get('created', datetime.now().isoformat()),
                    'modified': datetime.now().isoformat()
                }
                
                # Escribir archivo actualizado
                with open(prompt_file, 'w', encoding='utf-8') as f:
                    f.write('---\n')
                    yaml.dump(prompt_content, f, allow_unicode=True, sort_keys=False)
                    f.write('---\n')
                    f.write(data['content'])
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
                
            except Exception as e:
                print(f"Error updating prompt: {str(e)}")
                self.send_error(500, f"Error interno del servidor: {str(e)}")
        else:
            self.send_error(404)

    def list_prompts(self):
        prompts = []
        prompts_dir = os.path.join(os.getcwd(), 'prompts')
        
        if not os.path.exists(prompts_dir):
            return prompts

        for filename in os.listdir(prompts_dir):
            if filename.endswith('.md'):
                file_path = os.path.join(prompts_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
                        if match:
                            metadata = yaml.safe_load(match.group(1))
                            prompts.append({
                                'id': filename[:-3],
                                'title': str(metadata.get('title', 'Sin título')),
                                'tags': list(metadata.get('tags', [])),
                                'uses': int(metadata.get('uses', 0)),
                                'created': format_date(metadata.get('created')),
                                'modified': format_date(metadata.get('modified'))
                            })
                except Exception as e:
                    print(f"Error processing file {filename}: {str(e)}")
                    continue
        
        return prompts

def run(server_class=HTTPServer, handler_class=PromptHandler, port=8800):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)

    def signal_handler(signum, frame):
        print("\nApagando el servidor...")
        httpd.shutdown()
        httpd.server_close()
        print("Servidor detenido.")
        sys.exit(0)

    # Registrar manejadores para SIGINT (Ctrl+C) y SIGTERM
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"Servidor iniciado en http://localhost:{port}")
    print("Presiona Ctrl+C para detener")
    
    try:
        # Ejecutar el servidor en un hilo separado
        import threading
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True  # El hilo se cerrará cuando el programa principal termine
        server_thread.start()
        
        # Mantener el programa principal ejecutándose
        while True:
            signal.pause()  # Esperar señales
    except KeyboardInterrupt:
        pass
    finally:
        print("\nDeteniendo el servidor...")
        httpd.shutdown()
        httpd.server_close()
        print("Servidor detenido.")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8800
    run(port=port)
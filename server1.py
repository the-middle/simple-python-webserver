import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
import re
import os
import smtplib
import datetime
import psycopg2
from psycopg2 import Error
import yaml


hostName = os.getenv("SERVER_HOST", default="localhost")
serverPort = int(os.getenv("SERVER_PORT", default="8080"))
email_login = os.getenv("EMAIL_LOGIN", default="test@domain.com")
email_password = os.getenv("EMAIL_PASSWORD", default="qwerty")
smtp_server = os.getenv("SMTP_SERVER", default="smtp.gmail.com")
smtp_server_port = int(os.getenv("SMTP_SERVER_PORT", default="587"))
email_reciever = os.getenv("EMAIL_RECIEVER", default="test@domain.com")
db_user = os.getenv("DB_USER", default="postgres")
db_password = os.getenv("DB_PASSWORD", default="test1")
db_host = os.getenv("DB_HOST", default="127.0.0.1")
db_port = os.getenv("DB_PORT", default="5432")
db_name = os.getenv("DB_NAME", default="app")

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if re.search(r"/\?\d+=x", self.path):
            self.send_response(200)
            self.end_headers()
            x = re.search(r"\d+", self.path)
            x = pow(int(x[0]), 2)
            self.wfile.write(bytes(f"{x}", "utf-8"))
        elif re.search(r'/blacklisted', self.path):
            self.send_error(444, "You are blocked! Get outa here!")
            self.update_blocked_table()
            self.get_blocked_ips()
            self.generate_policy()
            self.block_ip_kubectl()
            # self.send_email_alert()

    def block_ip_kubectl(self):
        subprocess.run(["kubectl", "apply", "-f", f"{os.path.abspath(os.getcwd())}/network_policy.yml"])
    
    def send_email_alert(self):
        try: 
            smtp = smtplib.SMTP(smtp_server, smtp_server_port) 
            smtp.starttls() 
            smtp.login(email_login, email_password)
            message = f"Subject: Another one bites the dust!\n\nBlocked ip is: {self.client_address[0]}" 
            smtp.sendmail(email_login, email_reciever, message) 
            smtp.quit() 
            print("Email sent successfully!") 

        except Exception as ex: 
            print("Something went wrong....",ex)

    def create_table_db():
        try:
            connection = psycopg2.connect(user=db_user,
                                        password=db_password,
                                        host=db_host,
                                        port=db_port,
                                        database=db_name)
            cursor = connection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS blocked_ip (id SERIAL PRIMARY KEY, url_path TEXT NOT NULL, ip cidr NOT NULL, datetime timestamp(3) with time zone NOT NULL);")
            connection.commit()

        except (Exception, Error) as error:
            print("Error while connecting to PostgreSQL", error)
        finally:
            if (connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")

    def get_blocked_ips(self):
        try:
            connection = psycopg2.connect(user=db_user,
                                        password=db_password,
                                        host=db_host,
                                        port=db_port,
                                        database=db_name)
            cursor = connection.cursor()
            cursor.execute("SELECT ip FROM blocked_ip;")
            result = cursor.fetchall()

        except (Exception, Error) as error:
            print("Error while connecting to PostgreSQL", error)
        finally:
            if (connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")
        return result
    
    def update_blocked_table(self):
        current_datetime = datetime.datetime.now()
        try:
            connection = psycopg2.connect(user=db_user,
                                        password=db_password,
                                        host=db_host,
                                        port=db_port,
                                        database=db_name)
            cursor = connection.cursor()
            cursor.execute(f"INSERT INTO blocked_ip VALUES (DEFAULT, '{self.path}', '{self.client_address[0]}', '{current_datetime}');")
            connection.commit()

        except (Exception, Error) as error:
            print("Error while connecting to PostgreSQL", error)
        finally:
            if (connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")
    
    def generate_policy(self):
        dynamic_data = []
        for x in self.get_blocked_ips():
            dynamic_data += {
                    'from': [{
                        'ipBlock': {
                            'cidr': x[0],
                        },
                    },],
                },
        static_data = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'NetworkPolicy',
            'metadata': {
                'name': 'block-ips',
                'namespace': 'default',
            },
            'spec':{
                'podSelector': {},
                'policyTypes': ['Ingress',],
                'ingress': dynamic_data
            },
        }

        with open('network_policy.yml', 'w') as outfile:
            yaml.dump(static_data, outfile, default_flow_style=False)

if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print(f"Server started http://{hostName}:{serverPort}/?5=x")

    try:
        MyServer.create_table_db()
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
# coding=utf-8
import sys
import socket
import getopt
import threading
import subprocess

# Variaveis globais
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0


def usage():
    print("Hugo Netcat Tool")
    print("O que estiver em MAISCULO não faz parte literal do script, tem que ser substituido pelo o que convem")
    print("\n")
    print("usage: hnt.py -t HOST_ALVO -p PORTA")
    print(
        "-l --listen      - listen on [host]:[port] for incomming connections")
    print("\n")
    print("-e --execute=ARQUIVO_A_SER_EXECUTADO         - execute the ARQUIVO_A_SER_EXECUTADO as soon as a connection is established")
    print("\n")
    print("-c --command     - initialize a command shell")
    print("\n")
    print("-u --upload=DIRETÓRIO_DESTINO        - as soon as a connection is received, upload a file and write to DIRETÓRIO_DESTINO")
    print("\n \n")
    print("Examples: ")
    print("hnct.py -t 192.168.0.120 -p 5555 -l -c")
    print("hnct.py -t 192.168.0.120 -p 5555 -l -u=c:\\ARQUIVO.EXE")
    print("hnct.py -t 192.168.0.120 -p 5555 -l -e=\"CAT /ETC/PASSWD\"")
    print("echo 'ESCREVI E SAI CORRENDO' | ./hnct.py -t 192.168.20.26 -p 135")
    sys.exit(0)


def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        #   conecta ao host alvo
        client.connect((target, port))
        if len(buffer):
            client.send(buffer)
        while True:
            # agora espera receber dados de volta
            recv_len = 1
            response = ""
            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response = response + data

                if recv_len < 4096:
                    break
            print(response,)

            # espera mais dados de entrada
            buffer = input("")
            buffer = buffer + "\n"

            # envia os dados
            client.send(buffer)
    except err:
        print("[!] Deu ruim! Saindo...")
        # encerra a conexão
        client.close()


def server_loop():
    global target
    # se não houver nenhum alvo definido, ouviremos todas as interfaces
    if not len(target):
        target = "0.0.0.0"
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    while True:

        client_socket, addr = server.accept()
        # dispara uma thread para cuidar de nosso novo cliente
        client_thread = threading.Thread(
            target=client_handler,
            args=(client_socket,)
        )
        client_thread.start()


def run_command(command):
    # Remove a quebra de linha
    command = command.rstrip()

    # Executa o comando e obtém os dados de saída
    try:
        output = subprocess.check_output(
            command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "failed to execute command. \r\n"

    # envia os dados de saída de volta ao cliente
    return output


def client_handler(client_socket):
    global upload
    global execute
    global command

    # verifica se é upload
    if len(upload_destination):

        # Lê todos os bytes e grava em nosso destino
        file_buffer = ""

        # Permanece lendo os dados até que não haja mais nenhum disponível
        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            else:
                file_buffer = file_buffer + data
        # Agora tentamos gravar esses bytes
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            # Confirma que o arquivo foi gravado
            client_socket.send(
                "[*]Arquivo salvo com sucesso em %s\r\n") % (upload_destination)
        except:
            client_socket.send("[!]Falha ao salvar arquivo em %s\r\n") % (
                upload_destination)
    if len(execute):

        # Executa o comando
        output = run_command(execute)

        client_socket.send(output)

    # Entra em outro laço se um shell de comandos foi solicitado
    if command:

        while True:
            # Mostra um prompt simples
            client_socket.send("<HNT:#> ")

            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)
            # envia a saida do comando de volta
            response = run_command(cmd_buffer)
            # envia a resposta de volta
            client_socket.send(response)


def main():

    # Declarando as globais
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()
    # Lê as opções da linha de comando
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:", [
                                   "help", "listen", "execute", "target", "port", "command", "upload"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--commandshell"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Deu bosta"

        if not listen and len(target) and port > 0:
            # lê o buffer da linha de comando
            # isso causará um bloqueio, portando envie um CTRL-D se não estiver enviando dados de entrada para sdtin
            buffer = sys.stdin.read()

            # send data off
            client_sender(buffer)

            # iremos ouvir a porta e, potencialmente, faremos upload de dados, executaremos comandos e deixaremos um shell
            # de acordo com as opções de linha de comando anteriores
        if listen:
            server_loop()


main()

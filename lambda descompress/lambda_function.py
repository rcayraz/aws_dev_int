import pyzipper
import boto3
from io import BytesIO

# Asegurándonos de que PASSWORD esté en formato bytes
PASSWORD = b"testing01"

def lambda_handler(event, context):
    # Verificación básica para asegurarnos de que 'Records' está en el evento
    if 'Records' not in event:
        return {
            'statusCode': 400,
            'body': 'El evento no contiene registros. Asegúrese de que esta función Lambda sea invocada por un evento S3 válido.'
        }
    
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # Comprobamos que el key comienza con "folder_name/DEV/"
    if not key.startswith("folder_name/DEV/"):
        return {
            'statusCode': 400,
            'body': 'Archivo no está en el directorio adecuado. Proceso finalizado.'
        }

    # Extraemos el nombre de la carpeta basándonos en la estructura del key
    parts = key.split('/')
    if len(parts) < 4 or not parts[3].endswith('.zip'):
        return {
            'statusCode': 400,
            'body': 'La estructura del archivo no es la esperada. Proceso finalizado.'
        }

    folder_name = parts[2]  # Esto nos dará el nombre de la carpeta creada

    s3 = boto3.client('s3')
    s3_object = s3.get_object(Bucket=bucket, Key=key)
    s3_data = s3_object['Body'].read()

    # Extraer archivos en el directorio /tmp
    with pyzipper.AESZipFile(BytesIO(s3_data)) as zip_ref:
        zip_ref.extractall(path='/tmp', pwd=PASSWORD)

        for file in zip_ref.namelist():
            if file.endswith('.zip'):
                with zip_ref.open(file, pwd=PASSWORD) as inner_zip_data:
                    with pyzipper.AESZipFile(BytesIO(inner_zip_data.read())) as inner_zip_ref:
                        for inner_file in inner_zip_ref.namelist():
                            file_data = inner_zip_ref.read(inner_file)
                            # Aquí nos aseguramos de que los archivos se coloquen dentro de la carpeta creada
                            s3_key = f"folder_name/DEV/{folder_name}/{inner_file}"
                            s3.put_object(Bucket=bucket, Key=s3_key, Body=file_data)

    return {
        'statusCode': 200,
        'body': f'Archivos descomprimidos con éxito en folder_name/DEV/{folder_name}/!'
    }

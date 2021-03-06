import os
from subprocess import run, Popen, PIPE

"""
Este código aquí sirve para simplificar el proceso de manejo de traducciones. Correr este código actualizará las 
traducciones y en el servidor, y en la computadora.

Funciona también (probablemente) para coordinar traducciones entre Zanata y Transifex, porque todavía no he decidido
cuál es mejor. 
"""

proyecto_transifex = 'tinamit'
leng_orig = 'es'
lenguas = {'ms', 'fr', 'ta', 'ur', 'nl', 'tzj', 'quc', 'cak'}

# El directorio de la documentación
dir_docs = os.path.split(os.path.realpath(__file__))[0]

lenguas.update(os.listdir(os.path.join(dir_docs, 'source', '_locale')))

# Primero, actualizamos los archivos de documentos para traducir (.pot), basado en el código más recién del programa
print('Actualizando el proyecto...')
run('make.bat gettext', cwd=dir_docs)
l_lengs = '-l ' + ' -l '.join(lenguas)

# Actualizamos traducciones ya hechas (documentos .po) con las nuevas cosas para traducir
run('sphinx-intl update -p build/locale {}'.format(l_lengs), cwd=dir_docs)

p = Popen('tx init', stdin=PIPE, cwd=dir_docs, shell=True)
p.stdin.write(b'y\n')
p.stdin.flush()
p.stdin.write(b'\n')
p.stdin.flush()

run('sphinx-intl update-txconfig-resources --pot-dir build/locale --transifex-project-name {}'
    .format(proyecto_transifex), cwd=dir_docs)

archivo_config_tx = os.path.join(dir_docs, '.tx', 'config')
final = []
with open(archivo_config_tx, mode='r') as d:
    for l in d.readlines():
        if l == 'source_lang = en\n' and leng_orig != 'en':
            final.append('source_lang = {}\n'.format(leng_orig))
        else:
            final.append(l)

with open(archivo_config_tx, mode='w') as d:
    d.truncate()
    d.writelines(final)

# Mandar cambios locales al servidor Zanata
print('Mandando traducciones actualizadas localmente a Zanata...')
run('zanata po push --copytrans --import-po', input=b'y', cwd=dir_docs)

# Traemos traducciones de Transifex y las mandamos a Zanata.
print('Actualizando con Transifex...')
run('tx pull -a', cwd=dir_docs)
print('Mandando traducciones de Transifex a Zanata...')
run('zanata po push --copytrans --import-po', input=b'y', cwd=dir_docs)

# Traemos las traducciones más recientes de Zanata
print('Verificando las traducciones más recientes en Zanata...')
run('zanata po pull', cwd=dir_docs)

# Mandar los documentos de traducciones actualizados al servidor Transifex
print('Mandando todo a Transifex también...')
run('tx push -s -t', cwd=dir_docs)

# Ver las estadísticas
print('Pidiendo estadísticas recientes de traducción (de Zanata)...')
run('zanata stats', cwd=dir_docs)

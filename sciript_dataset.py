from music21 import *
import pandas as pd
import numpy as np
from collections import Counter
import os

data = {
    "COMPOSITOR": [], # nome do compositor
    "QUANTIDADE_DO": [], # quantidade de notas 'x', nome autoexplicativo
    "QUANTIDADE_DO_SUST": [],
    "QUANTIDADE_RE":[],
    "QUANTIDADE_RE_SUST": [],
    "QUANTIDADE_MI": [],
    "QUANTIDADE_FA": [],
    "QUANTIDADE_FA_SUST": [],
    "QUANTIDADE_SOL": [],
    "QUANTIDADE_SOL_SUST": [],
    "QUANTIDADE_LA": [],
    "QUANTIDADE_LA_SUST": [],
    "QUANTIDADE_SI": [],
    "MEDIA_INTERVALOS":[], # média do intervalo entre as notas
    "MEDIA_CONTORNO": [], # "sobes e desces" na melodia
    "2_NOTAS_SEGUIDAS": [], # quantidade de ocorrencias de 2 notas seguidas
    "3_NOTAS_SEGUIDAS": [], # quantidade de ocorrencias de 3 notas seguidas
    "MEDIA_DURACAO_NOTAS": [], # media da duração que as notas são tocadas
    "MEDIA_DURACAO_PAUSAS": [],
    "INT_HARM_1": [],
    "INT_HARM_2": [],
    "INT_HARM_3": [],
    "INT_HARM_4": [], 
    "INT_HARM_5": [],
    "INT_HARM_6": [], 
    "INT_HARM_7": [],
    "INT_HARM_8": [],
    "INT_HARM_9": [],
    "INT_HARM_10": [],
    "INT_HARM_11": [],
    "INT_HARM_12": [], 
}


def pega_notas(stream_obj):
    notas = []
    for element in stream_obj.flatten().notes:
        if isinstance(element, note.Note):
            notas.append(element.pitch.midi)
        elif isinstance(element, chord.Chord):
            notas.append(max([p.midi for p in element.pitches]))
    return notas

def notas_independentes(stream_obj):
    nota_count = {i: 0 for i in range(12)}
    nome_notas=[
        "QUANTIDADE_DO", "QUANTIDADE_DO_SUST", "QUANTIDADE_RE",
        "QUANTIDADE_RE_SUST", "QUANTIDADE_MI", "QUANTIDADE_FA",
        "QUANTIDADE_FA_SUST","QUANTIDADE_SOL", "QUANTIDADE_SOL_SUST",
        "QUANTIDADE_LA", "QUANTIDADE_LA_SUST", "QUANTIDADE_SI"
    ]
    for element in stream_obj.flatten().notes:
        if isinstance(element, note.Note):
            pitch = element.pitch.midi % 12
            nota_count[pitch] += 1
    for i in range(12):
        data[nome_notas[i]].append(nota_count[i])

def calcula_media_intervalos(notas):
    intervalos = []
    for i in range(1, len(notas)):
        tamanho_intervalo = notas[i]-notas[i-1]
        intervalos.append(tamanho_intervalo)
    return np.mean(intervalos)

def calcula_contorno_melodico(notas):
    contorno = []
    for i in range(1, len(notas)):
        diff = notas[i]-notas[i-1]
        if diff > 0:
            contorno.append(1)
        elif diff<0:
            contorno.append(-1)
        else:
            contorno.append(0)
    return np.mean(contorno)

def calcula_numero_2_notas_seguidas(notas):
    contagem = 0
    for i in range(1, len(notas)):
        if notas[i] == notas[i-1]:
            contagem += 1
    return contagem

def calcula_numero_3_notas_seguidas(notas):
    contagem = 0
    for i in range(2, len(notas)):
        if notas[i] == notas[i-1] and notas[i-1] == notas[i-2]:
            contagem += 1
    return contagem

def calcula_media_duracao_notas(stream_obj):
    duracao = 0
    for element in stream_obj.flat.notes:
        if isinstance(element, note.Note) or isinstance(element, chord.Chord):
            duracao += element.quarterLength
    return duracao/len(stream_obj.flat.notes)

def pega_media_duracao_pausas(stream_obj):
    media = 0
    pausas = stream_obj.flatten().getElementsByClass('Rest')
    for pausa in pausas:
        media += pausa.quarterLength
    return media/len(pausas) if len(pausas) > 0 else 0

def distribuicao_intervalos_harmonicos(chords):
    intervalos = []
    for c in chords:
        if len(c.pitches) > 1:
            for i in range(len(c.pitches)):
                for j in range(i+1, len(c.pitches)):
                    intervalo = abs(c.pitches[i].midi - c.pitches[j].midi)
                    intervalos.append(intervalo)
    return Counter(intervalos)

def processa_midi(file_path):
    s = midi.MidiFile()
    s.open(file_path)
    s.read()
    s.close()
    base_midi = midi.translate.midiFileToStream(s)
    notas = pega_notas(base_midi)
    notas_independentes(base_midi)
    media_intervalos = calcula_media_intervalos(notas)
    data['MEDIA_INTERVALOS'].append(media_intervalos)
    contorno = calcula_contorno_melodico(notas)
    data['MEDIA_CONTORNO'].append(contorno)
    notasseguidas = calcula_numero_2_notas_seguidas(notas)
    data['2_NOTAS_SEGUIDAS'].append(notasseguidas)
    notasseguidas = calcula_numero_3_notas_seguidas(notas)
    data['3_NOTAS_SEGUIDAS'].append(notasseguidas)
    media_duracao = calcula_media_duracao_notas(base_midi)
    data['MEDIA_DURACAO_NOTAS'].append(media_duracao)
    media_pausas = pega_media_duracao_pausas(base_midi)
    data['MEDIA_DURACAO_PAUSAS'].append(media_pausas)
    chords = base_midi.chordify().recurse().getElementsByClass("Chord")
    dist_intervalos = distribuicao_intervalos_harmonicos(chords)
    for intervalo in range(1, 13):
        col = f"INT_HARM_{intervalo}"
        data.setdefault(col, []).append(dist_intervalos.get(intervalo, 0))

    bins = [0, 0.5, 1, 2, 4, float('inf')]
    labels = ['<0.5', '0.5-1', '1-2', '2-4', '>4']
    duracoes = [n.quarterLength for n in base_midi.flat.notes]
    hist, _ = np.histogram(duracoes, bins=bins)
    for i, label in enumerate(labels):
        col = f'NOTA_DURACAO_{label}'
        data.setdefault(col, []).append(hist[i])

    pausas = [r.quarterLength for r in base_midi.flat.getElementsByClass('Rest')]
    hist_pausa, _ = np.histogram(pausas, bins=bins)
    for i, label in enumerate(labels):
        col = f'PAUSA_DURACAO_{label}'
        data.setdefault(col, []).append(hist_pausa[i])
    data['COMPOSITOR'].append('Johann Sebastian Bach')


def processa_diretorio_midi(diretorio):
    for arquivo in os.listdir(diretorio):
        if arquivo.lower().endswith(('.mid', '.midi')):
            caminho_arquivo = os.path.join(diretorio, arquivo)
            processa_midi(caminho_arquivo)



processa_diretorio_midi('/home/positivetoad/projetos/ML/musica/projeto_TA/midi/bach2')  # Substitua pelo caminho do diretório com arquivos MIDI
df_novo = pd.DataFrame(data)

if os.path.exists("data.csv"):
    df_antigo = pd.read_csv("data.csv")
    df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
else:
    df_final = df_novo

df_final.to_csv("data.csv", index=False)



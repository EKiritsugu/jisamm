# 生成训练用数据集并且产生相应的json文件
import os
import soundfile
import numpy as np
import json

n_speakers_per_sex = 9 # default: 7
n_samples = 10  # default: 10
duration = 15  # default 15 seconds

# output filename pattern
output_dir = './samples/'
filename = 'chi_{sex}_{spkr}_{ind}.wav'

if not os.path.exists(output_dir):
    os.mkdir(output_dir)



# get data type and sampling frequency of dataset
tmp,_ = soundfile.read('./wsj/female-01.wav')
dtype = tmp.dtype
fs = 16000

# a blank segment to insert between sentences
lmin, lmax = int(0.5) * fs, int(2.5) * fs
def new_blank():
    return np.zeros(lmin + np.random.randint(lmin, lmax), dtype=dtype)

# keep track of metadata in a file
metadata = {
        'fs' : fs,
        'files' : [],
        'sorted' : {},
        }

wav_ori = os.listdir('./wsj/')
wav_ori = [speaker
for speaker in wav_ori if speaker.endswith('.wav')]

male_list = [speaker
for speaker in wav_ori if speaker.startswith('male')]
female_list = [speaker
for speaker in wav_ori if speaker.startswith('female')]

len_sample = fs * duration
# iterate over different speakers to create the concatenated sentences
for sex in ['male', 'female']:


    metadata['sorted'][sex] = {}
    

    if sex == 'male':
        for speaker in male_list[:n_speakers_per_sex]:

            sample_ori , _= soundfile.read('./wsj/'+speaker )
            l_sample = sample_ori.shape[0]
            speaker = speaker[:-4]

            metadata['sorted'][sex][speaker] = []

            n = 0
            while n < n_samples:

                start_dot = np.random.randint(0, l_sample-len_sample-1)
                sample_wav = sample_ori[start_dot : start_dot+len_sample]
                
                fn = filename.format(sex=sex, spkr=speaker, ind=n+1)
                soundfile.write(
                        os.path.join(output_dir, fn),
                        sample_wav,fs
                        )
                metadata['sorted'][sex][speaker].append(fn)
                metadata['files'].append(fn)
                n += 1

    elif sex =='female':
        for speaker in female_list[:n_speakers_per_sex]:

            

            sample_ori , _= soundfile.read('./wsj/'+speaker )
            l_sample = sample_ori.shape[0]

            speaker = speaker[:-4]

            metadata['sorted'][sex][speaker] = []

            n = 0
            while n < n_samples:

                start_dot = np.random.randint(0, l_sample-len_sample-1)
                sample_wav = sample_ori[start_dot : start_dot+len_sample]
                
                fn = filename.format(sex=sex, spkr=speaker, ind=n+1)
                soundfile.write(
                        os.path.join(output_dir, fn),

                        sample_wav,fs
                        )
                metadata['sorted'][sex][speaker].append(fn)
                metadata['files'].append(fn)
                n += 1
with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
    json.dump(metadata, f, indent=4)

import struct


class WavParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.num_channels = 0
        self.sample_rate = 0
        self.bits_per_sample = 0
        self.sample_width = 0
        self.frames = b''
        self._read_header()
        self._read_frames()

    def _read_header(self):
        with open(self.file_path, 'rb') as f:
            riff_id = f.read(4).decode('ascii')
            chunk_size = struct.unpack('<I', f.read(4))[0]
            wave_format = f.read(4).decode('ascii')
            if riff_id != 'RIFF' or wave_format != 'WAVE':
                raise ValueError("Недопустимый файл WAV")

            fmt_id = f.read(4).decode('ascii')
            fmt_size = struct.unpack('<I', f.read(4))[0]
            if fmt_id != 'fmt ':
                raise ValueError("Неверный fmt")
            audio_format = struct.unpack('<H', f.read(2))[0]
            self.num_channels = struct.unpack('<H', f.read(2))[0]
            self.sample_rate = struct.unpack('<I', f.read(4))[0]
            byte_rate = struct.unpack('<I', f.read(4))[0]
            block_align = struct.unpack('<H', f.read(2))[0]
            self.bits_per_sample = struct.unpack('<H', f.read(2))[0]
            self.sample_width = self.bits_per_sample // 8

            data_id = f.read(4).decode('ascii')
            self.data_size = struct.unpack('<I', f.read(4))[0]
            if data_id != 'data':
                f.seek(self.data_size, 1)
                data_id = f.read(4).decode('ascii')
                self.data_size = struct.unpack('<I', f.read(4))[0]
                if data_id != 'data':
                    raise ValueError("Data chunk not found")

    def _read_frames(self):
        with open(self.file_path, 'rb') as f:
            f.seek(40)
            self.frames = f.read(self.data_size)

    def getparams(self):
        return (self.num_channels, self.sample_width, self.sample_rate,
                len(self.frames) // (self.num_channels * self.sample_width))

    def getframerate(self):
        return self.sample_rate

    def getnframes(self):
        return len(self.frames) // (self.num_channels * self.sample_width)

    def write_wav(self, output_path, params, frames):
        num_channels, sampwidth, framerate, nframes = params
        bits_per_sample = sampwidth * 8
        byte_rate = framerate * num_channels * sampwidth
        block_align = num_channels * sampwidth

        with open(output_path, 'wb') as f:
            f.write(b'RIFF')
            chunk_size = 36 + len(frames)
            f.write(struct.pack('<I', chunk_size))
            f.write(b'WAVE')

            f.write(b'fmt ')
            f.write(struct.pack('<I', 16))
            f.write(struct.pack('<H', 1))
            f.write(struct.pack('<H', num_channels))
            f.write(struct.pack('<I', framerate))
            f.write(struct.pack('<I', byte_rate))
            f.write(struct.pack('<H', block_align))
            f.write(struct.pack('<H', bits_per_sample))

            f.write(b'data')
            f.write(struct.pack('<I', len(frames)))
            f.write(frames)

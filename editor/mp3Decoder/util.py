def get_bits(buffer, start_bit, slice_len):
    """
    Преобразует байты из буфера в биты.
    """
    end_bit = start_bit + slice_len - 1

    start_byte = start_bit >> 3
    end_byte = end_bit >> 3

    buff_copy = buffer.copy()

    buff_len = len(buffer)
    if end_byte >= buff_len:
        buff_copy.extend([0 for _ in range(end_byte - buff_len + 1)])

    bits = []
    for idx in range(start_byte, end_byte + 1):
        num = buff_copy[idx]
        out = [1 if num & (1 << (8 - 1 - n)) else 0 for n in range(8)]
        bits.extend(out)

    start_bit %= 8
    end_bit = start_bit + slice_len - 1

    bit_slice = bits[start_bit:end_bit + 1]

    result = 0

    bit_slice.reverse()

    for i in range(len(bit_slice)):
        result += (2 ** i) * bit_slice[i]

    return result


def get_mp3_audio_start_offset(buffer):
    """
    Проверяет наличие ID3v2-тега
    в начале MP3-файла,
    определяет его длину и
    возвращает смещение до начала аудиоданных.
    """
    if buffer[0] == 73 and buffer[1] == 68 and buffer[2] == 51:
        flags_byte = buffer[5]
        size_bytes = buffer[6:10]
        id3_size = 0
        for byte in size_bytes:
            id3_size = id3_size * 128 + (byte & 127)

        offset = id3_size + 10

        if (flags_byte >> 4) & 1:
            offset += 10

        return offset
    else:
        return 0

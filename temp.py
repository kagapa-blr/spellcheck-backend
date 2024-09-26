import string

# Corrected string
sp_char = (
        """೧^l=F–೬B#yJwfz•+2umE<'!CxULvr]8o೦VNd0hH‘_>)- :sYQ7.g9n%W,G`1…"&?6೯I”೮೨Tb“@೭೫ʼKX4೪[iDScM;*t\’{5k/pa(PAeZ~O3R|j}q೩$"""
        + string.punctuation + 'ʼ“”•0123456789೧೨೩೪೫೬೭೮೯೦@#$%^&*()`_ʼ,.;ʼ' + ' ' + '"' + """'()*+,-./‘’’’“”;<=–>?@[\\]^_`{|}~""" + '…' + '“'
        + 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
)


# Check the unique characters (optional)
def unique_characters(s):
    seen = set()
    unique = []

    for char in s:
        if char not in seen:
            unique.append(char)
            seen.add(char)

    return ''.join(unique)


unique_sp_char = unique_characters(sp_char)
print(unique_sp_char)

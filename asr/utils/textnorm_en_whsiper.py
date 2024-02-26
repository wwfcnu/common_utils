from whisper.normalizers import EnglishTextNormalizer
import sys, os, argparse

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('ifile', help='input filename, assume utf-8 encoding')
    p.add_argument('ofile', help='output filename')
    p.add_argument('--to_upper', action='store_true', help='convert to upper case')
    p.add_argument('--to_lower', action='store_true', help='convert to lower case')
    p.add_argument('--has_key', action='store_true', help="input text has Kaldi's key as first field.")
    p.add_argument('--log_interval', type=int, default=10000, help='log interval in number of processed lines')
    args = p.parse_args()

    normalizer = EnglishTextNormalizer()

    n = 0
    with open(args.ifile, 'r',  encoding = 'utf8') as fi, open(args.ofile, 'w+', encoding = 'utf8') as fo:
        for line in fi:
            if args.has_key:
                cols = line.strip().split(maxsplit=1)
                key, text = cols[0].strip(), cols[1].strip() if len(cols) == 2 else ''
            else:
                text = line.strip()

            # whisper normalizer
            text = normalizer(text)


            # Cases
            if args.to_upper and args.to_lower:
                sys.stderr.write('text norm: to_upper OR to_lower?')
                exit(1)
            if args.to_upper:
                text = text.upper()
            if args.to_lower:
                text = text.lower()

            if args.has_key:
                print(key + '\t' + text, file = fo)
            else:
                print(text, file = fo)

            n += 1
            if n % args.log_interval == 0:
                print(f'text norm: {n} lines done.', file = sys.stderr)
    print(f'text norm: {n} lines done in total.', file = sys.stderr)

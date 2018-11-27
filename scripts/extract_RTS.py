from Radiomics.utils.rt import export_RTS
import argparse
import os


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--root', '-r', type=str)

    args = parser.parse_args()
    subjects = [x for x in os.listdir(args.root) if os.path.isdir(os.path.join(args.root, x))]
    
    for sub in subjects:
        print('\nProcessing subject: {}'.format(sub))
        export_RTS(os.path.join(args.root, sub))

    print('Done!')
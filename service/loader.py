from datasets import load_dataset


def load_taco_dataset(data_files):
    ds = load_dataset('arrow', split='train', data_files=data_files)
    return list(ds)
# crowdastro
Machine learning using crowd sourced data in astronomy.

For setup details, see the documentation [here](docs/setup.md), in particular start
[mongodb](https://www.mongodb.com/).
```bash
mongod --config /usr/local/etc/mongod.conf --fork
```

For a brief description of each notebook, see the documentation [here](docs/notebooks.md).

## Running the pipeline

Import data sources:

```bash
python3 -m crowdastro.import_data
```

Process the consensuses:

```bash
python3 -m crowdastro.consensuses
```

Generate the training data:

```bash
python3 -m crowdastro.generate_training_data
```

The training data contains `features` and `labels`. Note that image features have not been processed &mdash; these are raw pixels.

Generate a model:

```bash
python3 -m crowdastro.compile_cnn
```

Train the CNN:

```bash
python3 -m crowdastro.train_cnn
```

Generate the CNN outputs:

```bash
python3 -m crowdastro.generate_cnn_outputs
```

Note that this mutates the `features` dataset, replacing image features with the CNN outputs.

Repack the H5 file:

```bash
python3 crowdastro.repack_h5 training.h5
```

Train a logistic regression classifier:

```bash
python3 -m crowdastro.train_lr
```

Test the logistic regression classifier against subjects:

```bash
python3 -m crowdastro.test_lr
```

## Generating the Radio Galaxy Zoo catalogue

Process the consensuses as above, then generate the catalogue:

```bash
python -m crowdastro catalogue processed.db consensuses gator_cache hosts radio_components --atlas
```

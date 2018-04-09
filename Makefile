train: dataset
	python3 ./keras/train.py

tf-train: dataset
	python3 ./tf/train.py

regression: dataset
	python3 ./keras/train-regression.py

skipgrams: dataset
	python3 ./keras/train-skipgrams.py

dataset:
	npx ts-node ./bin/dataset.ts

clean:
	rm -rf out/*.raw
	rm -rf out/*.h5
	rm -rf logs/
	rm -rf images/

MODEL_WEIGHTS=$(wildcard out/gradtype-triplet-weights-*.h5)
PCA_IMAGES_PRE=$(subst out/gradtype-triplet-weights-,images/pca/, \
							 $(MODEL_WEIGHTS))
PCA_IMAGES=$(subst .h5,.png, $(PCA_IMAGES_PRE))

images/pca.mp4: visualize
	ffmpeg -v quiet -y -r 10 -pattern_type glob \
		-i "images/pca/*.png" \
		-vcodec libx264 -preset veryslow -pix_fmt yuv420p $@

visualize: images/pca $(PCA_IMAGES)

images/pca:
	mkdir -p images/pca

images/pca/%.png: out/gradtype-triplet-weights-%.h5
	python3 ./keras/visualize.py $< $@

.PHONY: train train-tf regression dataset clean visualize skipgrams

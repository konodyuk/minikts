mkdir ~/testdir
cd ~/testdir

templates=(
    classification/catboost
)

for name in "${templates[@]}"; do
    echo "testing $name"
    rm -rf ./*
    minikts template "$name"
    pip install -r src/requirements.txt
    python src/main.py train test
done

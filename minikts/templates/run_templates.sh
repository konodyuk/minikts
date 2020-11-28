mkdir ~/testdir
cd ~/testdir

templates=(
    classification/catboost
)

for name in "${!templates[@]}"; do
    rm -rf ./*
    minikts template "$name"
    pip install -r requirements.txt
    python src/main.py train test
done

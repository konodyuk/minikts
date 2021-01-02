mkdir ./testdir
cd ./testdir

templates=(
    catboost
)

for name in "${templates[@]}"; do
    echo "testing $name"
    rm -rf ./*
    minikts template "$name"
    python3 src/main.py train test
done

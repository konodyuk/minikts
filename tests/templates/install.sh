templates=(
    catboost
)

for name in "${templates[@]}"; do
    echo "installing requirements for $name"
    pip install -r minikts/templates/$name/requirements.txt
done

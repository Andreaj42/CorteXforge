mkdir -p timelines

for seed in {1..20}; do
    echo "=== Génération avec seed=$seed ==="

    cortexforge planner \
        --username andrea_joly \
        --duration 30 \
        --modulations OOK,4ASK,8ASK,BPSK,QPSK,8PSK,16PSK,32PSK,16APSK,32APSK,64APSK,128APSK,16QAM,32QAM,64QAM,128QAM,256QAM,AM-SSB-WC,AM-SSB-SC,AM-DSB-WC,AM-DSB-SC,FM,GMSK,OQPSK \
        --n-signals 240 \
        --seed "$seed"

    mv configs/timeline.csv "timelines/timeline_seed_${seed}.csv"
done
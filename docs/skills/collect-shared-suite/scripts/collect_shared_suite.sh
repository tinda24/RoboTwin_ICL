#!/bin/bash
# Queue the verified shared-table tasks, 50 episodes each.
# Existing seed.txt / hdf5 are continued, not deleted.
# Usage, from the repo root:
#   bash docs/skills/collect-shared-suite/scripts/collect_shared_suite.sh 2 3 5 6
set -u
cd /mnt/pre02/data/hqd/ICL_related/RoboTwin_ICL
export PATH=/mnt/pre02/data/hqd/miniconda3/envs/RoboTwin_ICL/bin:$PATH
export PYTHONUNBUFFERED=1

if [ "$#" -lt 1 ]; then
  echo "usage: $0 GPU [GPU ...]" >&2
  exit 2
fi

if ps -eo cmd | awk '/collect_data.py/ && /shared_suite/ && !/awk/ {found=1} END {exit !found}'; then
  echo "shared_suite collection is already running; not starting another copy" >&2
  exit 1
fi

tasks=(
  shared_place_cube
  shared_place_green_pad
  shared_place_cup_pad
  shared_place_cards_pad
  shared_stack_green_red
  shared_stack_red_green
  shared_stack_blue_green
  shared_place_red_yellow
  shared_place_cards_plate
  shared_place_cup_plate
  shared_place_green_blue
  shared_place_can_pad
  shared_press_button
  shared_turn_knob_cw
  shared_turn_knob_ccw
  shared_push_cards
  shared_push_red_pad
  shared_lift_green_cup
  shared_lift_red_cards
  shared_pinch_hammer
  shared_pinch_scanner
  shared_press_bell
  shared_lift_roller
)

gpus=("$@")
mkdir -p /tmp/suite_logs
echo "QUEUE $(date -Is) gpus=${gpus[*]}" >> /tmp/suite_logs/collect50_queue.log

run_one() {
  local gpu=$1
  shift
  for task in "$@"; do
    echo "START $(date -Is) $task gpu=$gpu" >> /tmp/suite_logs/collect50_queue.log
    bash collect_data.sh "$task" shared_suite "$gpu" > "/tmp/suite_logs/collect50_${task}.log" 2>&1
    echo "END $(date -Is) $task exit=$?" >> /tmp/suite_logs/collect50_queue.log
  done
}

for ((i = 0; i < ${#gpus[@]}; i++)); do
  group=()
  for ((j = i; j < ${#tasks[@]}; j += ${#gpus[@]})); do
    group+=("${tasks[$j]}")
  done
  run_one "${gpus[$i]}" "${group[@]}" &
done
wait
echo "ALL_COLLECT_DONE $(date -Is)" >> /tmp/suite_logs/collect50_queue.log

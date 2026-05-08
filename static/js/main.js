document.addEventListener("DOMContentLoaded", function () {
  initToasts();
  initTaskModal();
  initEventAddRepeatForm();
  initEventEditModal();
  initTagPointsRadar();
});

function initToasts() {
  const toasts = document.querySelectorAll(".toast-container .toast");
  if (!toasts.length) {
    return;
  }

  const hideDelayMs = 2800;
  const fadeDurationMs = 350;
  toasts.forEach(function (toast, index) {
    const delay = hideDelayMs + index * 120;
    window.setTimeout(function () {
      toast.classList.add("hide");
      window.setTimeout(function () {
        toast.remove();
      }, fadeDurationMs);
    }, delay);
  });
}

function initTaskModal() {
  const modal = document.getElementById("task-edit-modal");
  const taskButtons = document.querySelectorAll(".task-name-trigger");
  const editForm = document.getElementById("task-edit-form");
  const deleteForm = document.getElementById("task-delete-form");
  const deleteTrigger = document.getElementById("task-delete-trigger");
  const reasonText = document.getElementById("edit-task-reason");

  if (!modal || !taskButtons.length || !editForm || !deleteForm || !deleteTrigger || !reasonText) {
    return;
  }

  const fieldMap = {
    task_name: document.getElementById("edit-task-name"),
    tag: document.getElementById("edit-task-tag"),
    task_type: document.getElementById("edit-task-type"),
    deadline: document.getElementById("edit-task-deadline"),
    estimated_hours: document.getElementById("edit-task-estimated-hours"),
    difficulty: document.getElementById("edit-task-difficulty"),
    importance: document.getElementById("edit-task-importance"),
    status: document.getElementById("edit-task-status"),
    note: document.getElementById("edit-task-note")
  };

  function openModal() {
    modal.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = "";
  }

  taskButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      let task = {};
      try {
        task = JSON.parse(button.dataset.task || "{}");
      } catch (_err) {
        return;
      }

      if (!task.task_id) {
        return;
      }

      setValue(fieldMap.task_name, task.task_name);
      setValue(fieldMap.tag, task.tag);
      setValue(fieldMap.task_type, task.task_type || "事务");
      setValue(fieldMap.deadline, task.deadline);
      setValue(fieldMap.estimated_hours, task.estimated_hours);
      setValue(fieldMap.difficulty, task.difficulty || "1");
      setValue(fieldMap.importance, task.importance || "1");
      setValue(fieldMap.status, task.status || "未完成");
      setValue(fieldMap.note, task.note);

      reasonText.textContent = task.reason || "暂无推荐理由";
      editForm.action = "/tasks/update/" + task.task_id;
      deleteForm.action = "/tasks/delete/" + task.task_id;

      openModal();
    });
  });

  deleteTrigger.addEventListener("click", function () {
    deleteForm.submit();
  });

  modal.querySelectorAll("[data-modal-close]").forEach(function (el) {
    el.addEventListener("click", closeModal);
  });

  modal.addEventListener("click", function (event) {
    if (event.target === modal) {
      closeModal();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !modal.hidden) {
      closeModal();
    }
  });
}

function initEventAddRepeatForm() {
  const form = document.getElementById("event-add-form");
  if (!form) {
    return;
  }

  const isRepeatedSelect = document.getElementById("event-is-repeated");
  const repeatSettings = document.getElementById("event-repeat-settings");
  const repeatFrequency = document.getElementById("event-repeat-frequency");
  const repeatCountWrap = document.getElementById("event-repeat-count-wrap");
  const repeatUntilWrap = document.getElementById("event-repeat-until-wrap");
  const repeatCountInput = document.getElementById("event-repeat-count");
  const repeatUntilInput = document.getElementById("event-repeat-until");

  function toggleRepeatSettings() {
    const isRepeated = (isRepeatedSelect.value || "false") === "true";
    repeatSettings.hidden = !isRepeated;

    if (!isRepeated) {
      repeatCountInput.required = false;
      repeatUntilInput.required = false;
      return;
    }

    const selectedEndType = form.querySelector('input[name="repeat_end_type"]:checked');
    const endType = selectedEndType ? selectedEndType.value : "count";
    const useCount = endType === "count";
    repeatCountWrap.hidden = !useCount;
    repeatUntilWrap.hidden = useCount;
    repeatCountInput.required = useCount;
    repeatUntilInput.required = !useCount;
  }

  isRepeatedSelect.addEventListener("change", toggleRepeatSettings);
  repeatFrequency.addEventListener("change", toggleRepeatSettings);
  form.querySelectorAll('input[name="repeat_end_type"]').forEach(function (el) {
    el.addEventListener("change", toggleRepeatSettings);
  });

  toggleRepeatSettings();
}

function initEventEditModal() {
  const modal = document.getElementById("event-edit-modal");
  const eventButtons = document.querySelectorAll(".event-name-trigger");
  const form = document.getElementById("event-edit-form");

  if (!modal || !eventButtons.length || !form) {
    return;
  }

  const fieldMap = {
    event_name: document.getElementById("edit-event-name"),
    event_type: document.getElementById("edit-event-type"),
    date: document.getElementById("edit-event-date"),
    start_time: document.getElementById("edit-event-start-time"),
    end_time: document.getElementById("edit-event-end-time"),
    is_repeated: document.getElementById("edit-event-is-repeated"),
    note: document.getElementById("edit-event-note")
  };

  const updateScopeWrap = document.getElementById("event-update-scope-wrap");
  const repeatSettings = document.getElementById("event-edit-repeat-settings");
  const repeatFrequency = document.getElementById("edit-event-repeat-frequency");
  const repeatCountWrap = document.getElementById("edit-event-repeat-count-wrap");
  const repeatUntilWrap = document.getElementById("edit-event-repeat-until-wrap");
  const repeatCountInput = document.getElementById("edit-event-repeat-count");
  const repeatUntilInput = document.getElementById("edit-event-repeat-until");
  let sourceIsRepeated = false;

  function openModal() {
    modal.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = "";
  }

  function toggleEventEditRepeatSettings() {
    const scopeChecked = form.querySelector('input[name="update_scope"]:checked');
    const selectedScope = scopeChecked ? scopeChecked.value : "single";
    const isGroup = selectedScope === "group";
    const targetIsRepeated = (fieldMap.is_repeated.value || "false") === "true";

    updateScopeWrap.hidden = !sourceIsRepeated;
    const canShowRepeatSettings = sourceIsRepeated ? (isGroup && targetIsRepeated) : targetIsRepeated;
    repeatSettings.hidden = !canShowRepeatSettings;

    if (!canShowRepeatSettings) {
      repeatCountInput.required = false;
      repeatUntilInput.required = false;
      return;
    }

    const selectedEndType = form.querySelector('input[name="repeat_end_type"]:checked');
    const endType = selectedEndType ? selectedEndType.value : "count";
    const useCount = endType === "count";
    repeatCountWrap.hidden = !useCount;
    repeatUntilWrap.hidden = useCount;
    repeatCountInput.required = useCount;
    repeatUntilInput.required = !useCount;
  }

  function setEditScope(scope) {
    const target = form.querySelector('input[name="update_scope"][value="' + scope + '"]');
    if (target) {
      target.checked = true;
    }
  }

  eventButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      let event = {};
      try {
        event = JSON.parse(button.dataset.event || "{}");
      } catch (_err) {
        return;
      }

      if (!event.event_id) {
        return;
      }

      setValue(fieldMap.event_name, event.event_name);
      setValue(fieldMap.event_type, event.event_type || "其他");
      setValue(fieldMap.date, event.date);
      setValue(fieldMap.start_time, event.start_time);
      setValue(fieldMap.end_time, event.end_time);
      setValue(fieldMap.note, event.note);
      setValue(fieldMap.is_repeated, toBool(event.is_repeated) ? "true" : "false");

      form.action = "/events/update/" + event.event_id;
      setValue(repeatFrequency, "weekly");
      setValue(repeatCountInput, "1");
      setValue(repeatUntilInput, "");
      setEditScope("single");

      sourceIsRepeated = toBool(event.is_repeated);

      toggleEventEditRepeatSettings();
      openModal();
    });
  });

  fieldMap.is_repeated.addEventListener("change", toggleEventEditRepeatSettings);
  repeatFrequency.addEventListener("change", toggleEventEditRepeatSettings);
  form.querySelectorAll('input[name="repeat_end_type"]').forEach(function (el) {
    el.addEventListener("change", toggleEventEditRepeatSettings);
  });
  form.querySelectorAll('input[name="update_scope"]').forEach(function (el) {
    el.addEventListener("change", toggleEventEditRepeatSettings);
  });

  modal.querySelectorAll("[data-event-modal-close]").forEach(function (el) {
    el.addEventListener("click", closeModal);
  });

  modal.addEventListener("click", function (event) {
    if (event.target === modal) {
      closeModal();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !modal.hidden) {
      closeModal();
    }
  });
}

function setValue(el, value) {
  if (!el) {
    return;
  }
  el.value = value === null || value === undefined ? "" : String(value);
}

function toBool(value) {
  if (typeof value === "boolean") {
    return value;
  }
  const text = String(value || "").trim().toLowerCase();
  return text === "true" || text === "1" || text === "yes" || text === "y" || text === "是";
}

function initTagPointsRadar() {
  const canvas = document.getElementById("tag-points-radar");
  const payloadNode = document.getElementById("tag-points-radar-data");

  if (!canvas || !payloadNode) {
    return;
  }
  if (typeof Chart === "undefined") {
    return;
  }

  let payload = null;
  try {
    payload = JSON.parse(payloadNode.textContent || "{}");
  } catch (_err) {
    return;
  }

  const labels = Array.isArray(payload.labels) ? payload.labels : [];
  const scaledPoints = Array.isArray(payload.scaled_points) ? payload.scaled_points : [];
  const rawPoints = Array.isArray(payload.raw_points) ? payload.raw_points : [];
  const chartType = payload.chart_type === "bar" ? "bar" : "radar";

  if (!labels.length) {
    return;
  }
  if (chartType === "radar" && labels.length !== scaledPoints.length) {
    return;
  }
  if (chartType === "bar" && labels.length !== rawPoints.length) {
    return;
  }

  const tooltipRawPoints = rawPoints.length === labels.length ? rawPoints : scaledPoints.map(function () {
    return 0;
  });

  try {
    const commonTooltip = {
      callbacks: {
        label: function (context) {
          const index = context.dataIndex;
          const label = labels[index] || "未命名标签";
          const points = tooltipRawPoints[index] || 0;
          return [label, "累计获得积分：" + points];
        }
      }
    };

    if (chartType === "bar") {
      new Chart(canvas, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            {
              data: rawPoints,
              backgroundColor: "rgba(37, 99, 235, 0.35)",
              borderColor: "rgba(37, 99, 235, 0.9)",
              borderWidth: 1.5,
              borderRadius: 6
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              ticks: {
                color: "#334155"
              },
              grid: {
                color: "rgba(148, 163, 184, 0.2)"
              }
            },
            y: {
              beginAtZero: true,
              ticks: {
                color: "#64748b"
              },
              grid: {
                color: "rgba(148, 163, 184, 0.25)"
              }
            }
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: commonTooltip
          }
        }
      });
      return;
    }

    new Chart(canvas, {
      type: "radar",
      data: {
        labels: labels,
        datasets: [
          {
            data: scaledPoints,
            backgroundColor: "rgba(37, 99, 235, 0.18)",
            borderColor: "rgba(37, 99, 235, 0.9)",
            borderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 5,
            pointBackgroundColor: "rgba(30, 64, 175, 1)"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            min: 0,
            max: 5,
            ticks: {
              stepSize: 1,
              color: "#64748b",
              showLabelBackdrop: false
            },
            grid: {
              circular: true,
              color: "rgba(148, 163, 184, 0.35)"
            },
            angleLines: {
              color: "rgba(148, 163, 184, 0.45)"
            },
            pointLabels: {
              color: "#334155",
              font: {
                size: 12
              }
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: commonTooltip
        }
      }
    });
  } catch (_err) {
    // 图表初始化失败时静默降级，不影响页面其他功能。
  }
}

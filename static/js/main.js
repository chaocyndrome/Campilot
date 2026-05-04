document.addEventListener("DOMContentLoaded", function () {
  const toasts = document.querySelectorAll(".toast-container .toast");
  if (toasts.length) {
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

  function setValue(el, value) {
    if (!el) return;
    el.value = value === null || value === undefined ? "" : String(value);
  }

  taskButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      let task = {};
      try {
        task = JSON.parse(button.dataset.task || "{}");
      } catch (err) {
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
});

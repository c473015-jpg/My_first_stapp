// assets/app.js
// 가계부 관리 애플리케이션 로직
// 모든 DOM 조작은 textContent 사용, XSS 방지

(() => {
  const STORAGE_KEY = 'expense_tracker_data';
  const expenseForm = document.getElementById('expense-form');
  const expenseList = document.getElementById('expense-list');
  const totalAmountEl = document.getElementById('total-amount');

  // 로컬 스토리지에서 데이터 로드 (안전하게 파싱)
  function loadData() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      console.warn('저장된 데이터가 손상되었습니다. 초기화합니다.');
      localStorage.removeItem(STORAGE_KEY);
      return [];
    }
  }

  // 데이터 저장
  function saveData(data) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  }

  // 금액 검증 (숫자이고 양수인지)
  function validateAmount(value) {
    const num = Number(value);
    return isFinite(num) && num >= 0;
  }

  // 날짜 검증 (유효한 ISO 문자열)
  function validateDate(value) {
    return !isNaN(Date.parse(value));
  }

  // 전체 합계 계산 및 표시
  function updateTotal(data) {
    const total = data.reduce((sum, item) => sum + item.amount, 0);
    totalAmountEl.textContent = total.toLocaleString('ko-KR');
  }

  // 개별 항목 렌더링
  function renderItem(item, index) {
    const li = document.createElement('li');
    li.className = 'expense-item';
    li.dataset.idx = index;

    const dateSpan = document.createElement('span');
    dateSpan.textContent = new Date(item.date).toLocaleDateString('ko-KR');

    const categorySpan = document.createElement('span');
    categorySpan.textContent = item.category;

    const amountSpan = document.createElement('span');
    amountSpan.textContent = item.amount.toLocaleString('ko-KR') + ' 원';

    const noteSpan = document.createElement('span');
    noteSpan.textContent = item.note || '';

    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'actions';

    const editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.textContent = '수정';
    editBtn.addEventListener('click', () => editItem(index));

    const delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.textContent = '삭제';
    delBtn.addEventListener('click', () => deleteItem(index));

    actionsDiv.appendChild(editBtn);
    actionsDiv.appendChild(delBtn);

    li.appendChild(dateSpan);
    li.appendChild(categorySpan);
    li.appendChild(amountSpan);
    li.appendChild(noteSpan);
    li.appendChild(actionsDiv);
    expenseList.appendChild(li);
  }

  // 전체 리스트 새로 고침
  function renderList(data) {
    expenseList.innerHTML = '';
    data.forEach(renderItem);
    updateTotal(data);
  }

  // 폼 초기화
  function resetForm() {
    expenseForm.reset();
  }

  // 항목 추가 혹은 수정 핸들러
  function handleSubmit(event) {
    event.preventDefault();
    const date = expenseForm.date.value.trim();
    const category = expenseForm.category.value.trim();
    const amountStr = expenseForm.amount.value.trim();
    const note = expenseForm.note.value.trim();

    if (!validateDate(date) || !category || !validateAmount(amountStr)) {
      alert('입력값을 확인해주세요. 날짜와 금액이 올바른지 검증하세요.');
      return;
    }

    const amount = Number(amountStr);
    const data = loadData();
    const editingIdx = expenseForm.dataset.editing;

    if (editingIdx !== undefined) {
      // 기존 항목 수정
      data[editingIdx] = { date, category, amount, note };
      delete expenseForm.dataset.editing;
    } else {
      // 새 항목 추가
      data.push({ date, category, amount, note });
    }

    saveData(data);
    renderList(data);
    resetForm();
  }

  // 항목 삭제
  function deleteItem(idx) {
    const data = loadData();
    data.splice(idx, 1);
    saveData(data);
    renderList(data);
  }

  // 항목 수정 (폼에 값 채워서 편집 모드 전환)
  function editItem(idx) {
    const data = loadData();
    const item = data[idx];
    expenseForm.date.value = item.date;
    expenseForm.category.value = item.category;
    expenseForm.amount.value = item.amount;
    expenseForm.note.value = item.note || '';
    expenseForm.dataset.editing = idx; // 편집 중임을 표시
  }

  // 초기 로드
  expenseForm.addEventListener('submit', handleSubmit);
  renderList(loadData());
})();

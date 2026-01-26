<script setup>
import {ref, onMounted} from 'vue'

// 所有账单数据
const bills = ref([])

// 从后端加载账单
const loadBills = async () => {
  const res = await fetch('http://127.0.0.1:8000/bills')
  const data = await res.json()
  bills.value = data
}

const addBill = async () => {
  const newBill = {
    name: "测试账单",
    amount: 100,
    type: 'expense',
    date: new Date().toISOString().slice(0, 10)
  }
  const res = await fetch('http://127.0.0.1:8000/bills', {
    method: 'POST',
    headers: {'Content-Type': "application/json"},
    body: JSON.stringify(newBill)
  })
  const saved = await res.json()
  bills.value.push(saved)
}

const deleteBill = async (id) => {
  try {

    const res = await fetch(`http://127.0.0.1:8000/bills/${id}`, {method: "DELETE"})
    if(res.ok) {
      bills.value = bills.value.filter(b => b.id != id)
    } else {
      const error = await res.json()
      alert("删除失败：" + error.detail)
    }
  } catch (error) {
    console.error("删除请求失败：", error)
    alert("网络错误，删除失败")
  }
}

onMounted(() => {
  loadBills()
})

</script>

<template>
  <div class="max-w-2xl mx-auto p-4">
    <h1 class="text-2xl font-bold text-center mb-6">📝 账单管理器</h1>

    <button @click="addBill" class="bg-blue-600 text-white px-4 py-2 rounded mb-4">
      + 添加测试账单
    </button>

    <ul class="space-y-2">
      <li v-for="bill in bills" :key="bill.id"
          class="flex justify-between items-center p-3 border rounded bg-white">
        <span>
          {{ bill.name }} - ¥{{ bill.amount }}
          <em class="text-gray-500 text-sm">({{ bill.type === 'income' ? '收入' : '支出' }})</em>
        </span>
        <button @click="deleteBill(bill.id)" class="text-red-500 hover:text-red-700">🗑️</button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
  /* 可以稍后用 Tailwind 或 CSS 美化 */
  </style>

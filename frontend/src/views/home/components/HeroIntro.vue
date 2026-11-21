<script setup>
</script>

<template>
  <section>
    <h1>هر آنچه نیاز دارید<br /><span>همه رو یک‌جا رزرو کنید</span></h1>
    <p class="sub">از اقامت و سفر تا خدمات روزمره — هر برنامه‌ای را به نتیجه برسانید</p>
    <div class="search">
      <input placeholder="چه چیزی را می‌خواهید رزرو کنید؟" aria-label="جستجو" />
      <span class="all">&#9638; همه دسته‌ها &#8964;</span>
      <button aria-label="برو">&larr;</button>
    </div>
    <!-- CategoryTabs این‌جا می‌آید -->
    <slot />
  </section>
</template>
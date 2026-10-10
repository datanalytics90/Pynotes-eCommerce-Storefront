
document.addEventListener('DOMContentLoaded',()=>{
  const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add('show')}),{threshold:.12});
  document.querySelectorAll('.reveal').forEach(el=>observer.observe(el));

  const backdrop=document.querySelector('.cart-backdrop'), drawer=document.querySelector('.cart-drawer');
  const openCart=()=>{if(drawer){drawer.classList.add('open');backdrop?.classList.add('show')}};
  const closeCart=()=>{drawer?.classList.remove('open');backdrop?.classList.remove('show')};
  document.querySelectorAll('[data-open-cart]').forEach(b=>b.addEventListener('click',openCart));
  document.querySelectorAll('[data-close-cart]').forEach(b=>b.addEventListener('click',closeCart));
  backdrop?.addEventListener('click',closeCart);

  const count=document.querySelectorAll('[data-cart-count]');
  let cartCount=0;
  document.querySelectorAll('[data-add-cart]').forEach(btn=>{
    btn.addEventListener('click',()=>{
      cartCount++;
      count.forEach(c=>c.textContent=cartCount);
      const original=btn.innerHTML; btn.innerHTML='Added ✓'; btn.disabled=true;
      setTimeout(()=>{btn.innerHTML=original;btn.disabled=false},1100);
    });
  });
  document.querySelectorAll('[data-qty]').forEach(w=>{
    const input=w.querySelector('input'), minus=w.querySelector('[data-minus]'), plus=w.querySelector('[data-plus]');
    minus?.addEventListener('click',()=>input.value=Math.max(1,(+input.value||1)-1));
    plus?.addEventListener('click',()=>input.value=(+input.value||1)+1);
  });
});


// PyNotes premium motion helpers
(function(){
  const header=document.querySelector('.site-header');
  const updateHeader=()=>{
    if(!header)return;
    header.classList.toggle('scrolled',window.scrollY>20);
  };
  updateHeader();
  window.addEventListener('scroll',updateHeader,{passive:true});

  // Gentle pointer parallax for the hero book on desktop.
  const heroBook=document.querySelector('.hero-book');
  if(heroBook && window.matchMedia('(pointer:fine)').matches && !window.matchMedia('(prefers-reduced-motion: reduce)').matches){
    const max=7;
    heroBook.addEventListener('pointermove',(e)=>{
      const r=heroBook.getBoundingClientRect();
      const x=(e.clientX-r.left)/r.width-.5;
      const y=(e.clientY-r.top)/r.height-.5;
      heroBook.style.transform=`translateY(-6px) rotateY(${x*max}deg) rotateX(${y*-max}deg)`;
    });
    heroBook.addEventListener('pointerleave',()=>{
      heroBook.style.transform='';
    });
  }

  // Small ripple feedback on primary buttons.
  document.querySelectorAll('.btn-brand,.btn-teal').forEach(btn=>{
    btn.addEventListener('click',(e)=>{
      const rect=btn.getBoundingClientRect();
      const ripple=document.createElement('span');
      ripple.style.cssText=`position:absolute;border-radius:50%;pointer-events:none;width:12px;height:12px;background:rgba(255,255,255,.35);left:${e.clientX-rect.left-6}px;top:${e.clientY-rect.top-6}px;transform:scale(0);opacity:1;transition:transform .6s ease,opacity .6s ease`;
      btn.appendChild(ripple);
      requestAnimationFrame(()=>{ripple.style.transform='scale(18)';ripple.style.opacity='0'});
      setTimeout(()=>ripple.remove(),650);
    });
  });
})();

// Announcement bar rotator — cycles through admin-configured messages.
(function(){
  const items = document.querySelectorAll('.announcement [data-announcement]');
  if(items.length <= 1) return;
  let i = 0;
  setInterval(()=>{
    items[i].style.display = 'none';
    i = (i + 1) % items.length;
    items[i].style.display = '';
  }, 4500);
})();

// Add-to-cart forms submit over AJAX so the cart badge/drawer update without a page reload.
document.addEventListener('DOMContentLoaded', () => {
  function getCookie(name) {
    const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? match.pop() : '';
  }

  document.querySelectorAll('form[data-ajax-cart]').forEach((form) => {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const response = await fetch(form.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCookie('csrftoken') },
        body: new FormData(form),
      });
      if (response.ok) {
        const data = await response.json();
        document.querySelectorAll('[data-cart-count]').forEach((el) => { el.textContent = data.total_items; });
        if (data.cart_html) {
          document.querySelector('.cart-drawer').outerHTML = data.cart_html;
        }
      }
    });
  });
});

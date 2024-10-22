document.querySelector('.btn').addEventListener('mouseenter', () => {
    document.querySelector('.btn').classList.add('shake');
});

document.querySelector('.btn').addEventListener('mouseleave', () => {
    document.querySelector('.btn').classList.remove('shake');
});

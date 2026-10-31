// 안드로이드 + 블루투스 키보드에서 Tab이 문자로 입력되는 문제 방지: Tab/Shift+Tab을 직접 포커스 이동으로 처리
const FOCUSABLE = 'input:not([disabled]):not([type=hidden]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])';

export function tabNav(form) {
	function move(e, back) {
		const items = [...form.querySelectorAll(FOCUSABLE)].filter((el) => el.offsetParent !== null);
		const i = items.indexOf(document.activeElement);
		const next = items[i + (back ? -1 : 1)];
		if (i < 0 || !next) return false;
		e.preventDefault();
		next.focus();
		return true;
	}
	const onKeydown = (e) => {
		if (e.key === 'Tab' || e.keyCode === 9) move(e, e.shiftKey);
	};
	// IME가 keydown 대신 탭 문자를 삽입하는 경우
	const onBeforeInput = (e) => {
		if (e.data === '\t') move(e, false);
	};
	form.addEventListener('keydown', onKeydown);
	form.addEventListener('beforeinput', onBeforeInput);
	return {
		destroy() {
			form.removeEventListener('keydown', onKeydown);
			form.removeEventListener('beforeinput', onBeforeInput);
		}
	};
}

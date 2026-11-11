//#region \0rolldown/runtime.js
var e = Object.defineProperty, t = (t, n) => {
	let r = {};
	for (var i in t) e(r, i, {
		get: t[i],
		enumerable: !0
	});
	return n || e(r, Symbol.toStringTag, { value: "Module" }), r;
}, n = 0, r = 1, i = 2, a = 3, o = {
	name: "Latte",
	type: "light",
	palette: [
		"#dd7878",
		"#ea76cb",
		"#8839ef",
		"#e64553",
		"#fe640b",
		"#df8e1d",
		"#40a02b",
		"#209fb5",
		"#1e66f5",
		"#7287fd"
	],
	cssVar: {
		"--node-gap-x": "30px",
		"--node-gap-y": "10px",
		"--main-gap-x": "65px",
		"--main-gap-y": "45px",
		"--root-radius": "30px",
		"--main-radius": "20px",
		"--root-color": "#ffffff",
		"--root-bgcolor": "#4c4f69",
		"--root-border-color": "rgba(0, 0, 0, 0)",
		"--main-border": "",
		"--main-color": "#444446",
		"--main-bgcolor": "#ffffff",
		"--main-bgcolor-transparent": "rgba(255, 255, 255, 0.8)",
		"--topic-padding": "3px",
		"--color": "#777777",
		"--bgcolor": "#f6f6f6",
		"--selected": "#4dc4ff",
		"--accent-color": "#e64553",
		"--panel-color": "#444446",
		"--panel-bgcolor": "#ffffff",
		"--panel-border-color": "#eaeaea",
		"--map-padding": "50px 80px"
	}
}, s = {
	name: "Dark",
	type: "dark",
	palette: [
		"#848FA0",
		"#748BE9",
		"#D2F9FE",
		"#4145A5",
		"#789AFA",
		"#706CF4",
		"#EF987F",
		"#775DD5",
		"#FCEECF",
		"#DA7FBC"
	],
	cssVar: {
		"--node-gap-x": "30px",
		"--node-gap-y": "10px",
		"--main-gap-x": "65px",
		"--main-gap-y": "45px",
		"--root-radius": "30px",
		"--main-radius": "20px",
		"--root-color": "#ffffff",
		"--root-bgcolor": "#2d3748",
		"--root-border-color": "rgba(255, 255, 255, 0.1)",
		"--main-border": "",
		"--main-color": "#ffffff",
		"--main-bgcolor": "#4c4f69",
		"--main-bgcolor-transparent": "rgba(76, 79, 105, 0.8)",
		"--topic-padding": "3px",
		"--color": "#cccccc",
		"--bgcolor": "#252526",
		"--selected": "#4dc4ff",
		"--accent-color": "#789AFA",
		"--panel-color": "#ffffff",
		"--panel-bgcolor": "#2d3748",
		"--panel-border-color": "#696969",
		"--map-padding": "50px 80px"
	}
};
//#endregion
//#region src/utils/index.ts
function c(e) {
	return e.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
}
var l = function(e, t) {
	if (t.id === e) return t;
	if (t.children && t.children.length) {
		for (let n = 0; n < t.children.length; n++) {
			let r = l(e, t.children[n]);
			if (r) return r;
		}
		return null;
	}
	return null;
}, u = (e, t) => {
	if (e.parent = t, e.children) for (let t = 0; t < e.children.length; t++) u(e.children[t], e);
}, d = (e, t, n) => {
	if (e.expanded = t, e.children) if (n === void 0 || n > 0) {
		let r = n === void 0 ? void 0 : n - 1;
		e.children.forEach((e) => {
			d(e, t, r);
		});
	} else e.children.forEach((e) => {
		d(e, !1);
	});
};
function f(e) {
	if (e.id = m(), e.children) for (let t = 0; t < e.children.length; t++) f(e.children[t]);
}
function p(e, t, n, r) {
	let i = n - e, a = r - t, o = Math.atan2(a, i) * 180 / Math.PI, s = (o + 180 - 30) * Math.PI / 180, c = (o + 180 + 30) * Math.PI / 180;
	return {
		x1: n + Math.cos(s) * 12,
		y1: r + Math.sin(s) * 12,
		x2: n + Math.cos(c) * 12,
		y2: r + Math.sin(c) * 12
	};
}
function m() {
	return Date.now().toString(36) + Math.random().toString(36).substring(2, 8);
}
var h = function() {
	let e = m();
	return {
		topic: this.newTopicName,
		id: e
	};
};
function g(e) {
	return JSON.parse(JSON.stringify(e, (e, t) => {
		if (e !== "parent") return t;
	}));
}
var _ = (e, t) => {
	let n = 0, r = 0;
	for (; t && t !== e;) n += t.offsetLeft, r += t.offsetTop, t = t.offsetParent;
	return {
		offsetLeft: n,
		offsetTop: r
	};
}, v = (e, t) => {
	for (let n in t) e.setAttribute(n, t[n]);
}, y = (e) => e ? e.classList.contains("me-tpc") : !1, b = (e) => {
	let t = new Set(e.map((e) => e.nodeObj));
	return e.filter((e) => e.nodeObj.parent).filter((e) => {
		let n = e.nodeObj.parent;
		for (; n;) {
			if (t.has(n)) return !1;
			n = n.parent;
		}
		return !0;
	});
}, x = (e) => {
	let t = e.match(/translate3d\(([^,]+),\s*([^,]+)/);
	return t ? {
		x: parseFloat(t[1]),
		y: parseFloat(t[2])
	} : {
		x: 0,
		y: 0
	};
}, S = function(e) {
	for (let t = 0; t < e.length; t++) {
		let { dom: n, evt: r, func: i } = e[t];
		n.addEventListener(r, i);
	}
	return function() {
		for (let t = 0; t < e.length; t++) {
			let { dom: n, evt: r, func: i } = e[t];
			n.removeEventListener(r, i);
		}
	};
}, C = (e, t) => {
	let n = e.x - t.x, r = e.y - t.y;
	return Math.sqrt(n * n + r * r);
}, w = function(e, t) {
	if (!t) return T(e), e;
	let n = e.querySelector(".insert-preview"), r = `insert-preview ${t} show`;
	return n || (n = document.createElement("div"), e.appendChild(n)), n.className = r, e;
}, T = function(e) {
	if (!e) return;
	let t = e.querySelectorAll(".insert-preview");
	for (let e of t || []) e.remove();
}, E = function(e, t) {
	for (let n of t) {
		let t = n.parentElement.parentElement.contains(e);
		if (!(e && e.classList.contains("me-tpc") && e !== n && !t && e.nodeObj.parent)) return !1;
	}
	return !0;
}, D = function(e) {
	let t = document.createElement("div");
	return t.className = "mind-elixir-ghost", e.container.appendChild(t), t;
}, O = class {
	mind;
	isMoving = !1;
	interval = null;
	speed = 20;
	constructor(e) {
		this.mind = e;
	}
	move(e, t) {
		this.isMoving || (this.isMoving = !0, this.interval = setInterval(() => {
			this.mind.move(e * this.speed * this.mind.scaleVal, t * this.speed * this.mind.scaleVal);
		}, 100));
	}
	stop() {
		this.isMoving = !1, this.interval &&= (clearInterval(this.interval), null);
	}
};
function k(e) {
	return {
		isDragging: !1,
		insertType: null,
		meet: null,
		ghost: D(e),
		edgeMoveController: new O(e),
		startX: 0,
		startY: 0,
		pointerId: null
	};
}
var A = 5;
function j(e, t, n, r = !1) {
	if (e.spacePressed) return !1;
	let i = n.target;
	if (!i?.classList.contains("me-tpc") || !i.nodeObj.parent) return !1;
	if (t.startX = n.clientX, t.startY = n.clientY, t.pointerId = n.pointerId, e.dragged = e.currentNodes, r) {
		N(e, t);
		let r = e.container.getBoundingClientRect();
		M(t.ghost, n.clientX - r.x, n.clientY - r.y);
	}
	return !0;
}
function M(e, t, n) {
	e.style.transform = `translate(${t - 10}px, ${n - 10}px)`, e.style.display = "block";
}
function N(e, t) {
	let { dragged: n } = e;
	if (!n) return;
	let r = document.activeElement;
	r && r.isContentEditable && r.blur(), t.isDragging = !0, n.length > 1 ? t.ghost.innerHTML = n.length + "" : t.ghost.innerHTML = n[0].innerHTML;
	for (let e of n) e.parentElement.parentElement.style.opacity = "0.5";
	e.panHelper.clear();
}
function ee(e, t, n) {
	let { dragged: r } = e;
	if (!r || t.pointerId !== n.pointerId) return;
	let i = n.clientX - t.startX, a = n.clientY - t.startY, o = Math.sqrt(i * i + a * a);
	if (!t.isDragging && o > A && N(e, t), !t.isDragging) return;
	let s = e.container.getBoundingClientRect();
	M(t.ghost, n.clientX - s.x, n.clientY - s.y), n.clientX < s.x + 50 ? t.edgeMoveController.move(1, 0) : n.clientX > s.x + s.width - 50 ? t.edgeMoveController.move(-1, 0) : n.clientY < s.y + 50 ? t.edgeMoveController.move(0, 1) : n.clientY > s.y + s.height - 50 ? t.edgeMoveController.move(0, -1) : t.edgeMoveController.stop(), T(t.meet);
	let c = 12 * e.scaleVal;
	if (e.direction === 3) {
		let e = document.elementFromPoint(n.clientX - c, n.clientY);
		if (E(e, r)) {
			t.meet = e;
			let r = e.getBoundingClientRect();
			t.insertType = n.clientX > r.x + r.width ? "after" : "in";
		} else {
			let e = document.elementFromPoint(n.clientX + c, n.clientY);
			if (E(e, r)) {
				t.meet = e;
				let r = e.getBoundingClientRect();
				t.insertType = n.clientX < r.x ? "before" : "in";
			} else t.insertType = null, t.meet = null;
		}
		t.meet && w(t.meet, t.insertType);
		return;
	}
	let l = document.elementFromPoint(n.clientX, n.clientY - c);
	if (E(l, r)) {
		t.meet = l;
		let e = l.getBoundingClientRect(), r = e.y;
		t.insertType = n.clientY > r + e.height ? "after" : "in";
	} else {
		let e = document.elementFromPoint(n.clientX, n.clientY + c);
		if (E(e, r)) {
			t.meet = e;
			let r = e.getBoundingClientRect().y;
			t.insertType = n.clientY < r ? "before" : "in";
		} else t.insertType = null, t.meet = null;
	}
	t.meet && w(t.meet, t.insertType);
}
function te(e, t, n) {
	let { dragged: r } = e;
	if (!(!r || t.pointerId !== n.pointerId)) {
		t.edgeMoveController.stop();
		for (let e of r) e.parentElement.parentElement.style.opacity = "1";
		t.ghost.style.display = "none", t.ghost.innerHTML = "", t.isDragging && t.meet && (T(t.meet), t.insertType === "before" ? e.moveNodesBefore(r, t.meet) : t.insertType === "after" ? e.moveNodesAfter(r, t.meet) : t.insertType === "in" && e.moveNodesIn(r, t.meet)), e.dragged = null, t.isDragging = !1, t.insertType = null, t.meet = null, t.pointerId = null;
	}
}
function ne(e, t) {
	let { dragged: n } = e;
	if (n) {
		t.edgeMoveController.stop();
		for (let e of n) e.parentElement.parentElement.style.opacity = "1";
		t.meet && T(t.meet), t.ghost.style.display = "none", t.ghost.innerHTML = "", e.dragged = null, t.isDragging = !1, t.insertType = null, t.meet = null, t.pointerId = null;
	}
}
function re(e) {
	return () => {};
}
//#endregion
//#region src/types/index.ts
var P = {
	LHS: "lhs",
	RHS: "rhs",
	DOWN: "down"
}, ie = function() {
	this.nodes.innerHTML = "", this.nodes.classList.toggle("down", this.direction === 3);
	let e = this.createTopic(this.nodeData);
	ce.call(this, e, this.nodeData), e.draggable = !1;
	let t = document.createElement("div");
	t.className = "me-root", t.appendChild(e);
	let n = this.nodeData.children || [];
	if (this.direction === 2) {
		let e = 0, t = 0;
		n.map((n) => {
			n.direction === 0 ? e += 1 : n.direction === 1 ? t += 1 : e <= t ? (n.direction = 0, e += 1) : (n.direction = 1, t += 1);
		});
	}
	ae(this, n, t);
}, ae = function(e, t, n) {
	if (e.direction === 3) {
		let r = pe(P.DOWN);
		for (let n = 0; n < t.length; n++) {
			let { grp: i } = e.createWrapper(t[n]);
			r.appendChild(i);
		}
		e.nodes.appendChild(n), e.nodes.appendChild(r), e.nodes.appendChild(e.lines), e.nodes.appendChild(e.labelContainer);
		return;
	}
	let r = pe(P.LHS), i = pe(P.RHS);
	for (let n = 0; n < t.length; n++) {
		let a = t[n], { grp: o } = e.createWrapper(a);
		e.direction === 2 ? a.direction === 0 ? r.appendChild(o) : i.appendChild(o) : e.direction === 0 ? r.appendChild(o) : i.appendChild(o);
	}
	e.nodes.appendChild(r), e.nodes.appendChild(n), e.nodes.appendChild(i), e.nodes.appendChild(e.lines), e.nodes.appendChild(e.labelContainer);
}, oe = function(e, t) {
	let n = document.createElement("div");
	n.className = "me-children";
	for (let r = 0; r < t.length; r++) {
		let i = t[r], { grp: a } = e.createWrapper(i);
		n.appendChild(a);
	}
	return n;
}, se = function(e, t) {
	let n = (this?.el ? this.el : t || document).querySelector(`[data-nodeid="me${e}"]`);
	if (!n) throw Error(`FindEle: Node ${e} not found, maybe it's collapsed.`);
	return n;
}, ce = function(e, t) {
	if (e.innerHTML = "", t.style) {
		let n = t.style;
		for (let t in n) e.style[t] = n[t];
	}
	if (t.dangerouslySetInnerHTML) {
		e.innerHTML = t.dangerouslySetInnerHTML;
		return;
	}
	if (t.image) {
		let n = t.image;
		if (n.url && n.width && n.height) {
			let t = document.createElement("img");
			t.src = this.imageProxy ? this.imageProxy(n.url) : n.url, t.style.width = n.width + "px", t.style.height = n.height + "px", n.fit && (t.style.objectFit = n.fit), e.appendChild(t), e.image = t;
		} else console.warn("Image url/width/height are required");
	} else e.image &&= void 0;
	{
		let n = document.createElement("span");
		n.className = "text", this.markdown ? n.innerHTML = this.markdown(t.topic, t) : n.textContent = t.topic, e.appendChild(n), e.text = n;
	}
	if (t.hyperLink) {
		let n = document.createElement("a");
		n.className = "hyper-link", n.target = "_blank", n.innerText = "🔗", n.href = t.hyperLink, e.appendChild(n), e.link = n;
	} else e.link &&= void 0;
	if (t.icons && t.icons.length) {
		let n = document.createElement("span");
		n.className = "icons", n.innerHTML = t.icons.map((e) => `<span>${c(e)}</span>`).join(""), e.appendChild(n), e.icons = n;
	} else e.icons &&= void 0;
	if (t.tags && t.tags.length) {
		let n = document.createElement("div");
		n.className = "tags", t.tags.forEach((e) => {
			let t = document.createElement("span");
			typeof e == "string" ? t.textContent = e : (t.textContent = e.text, e.className && (t.className = e.className), e.style && Object.assign(t.style, e.style)), n.appendChild(t);
		}), e.appendChild(n), e.tags = n;
	} else e.tags &&= void 0;
}, le = function(e, t) {
	let n = document.createElement("div");
	n.className = "me-wrapper";
	let { p: r, tpc: i } = this.createParent(e);
	if (n.appendChild(r), !t && e.children && e.children.length > 0) {
		let t = _e(e.expanded);
		if (r.appendChild(t), e.expanded !== !1) {
			let t = oe(this, e.children);
			n.appendChild(t);
		}
	}
	return {
		grp: n,
		top: r,
		tpc: i
	};
}, ue = function(e) {
	let t = document.createElement("div");
	t.className = "me-parent";
	let n = this.createTopic(e);
	return ce.call(this, n, e), t.appendChild(n), {
		p: t,
		tpc: n
	};
}, de = function(e) {
	let t = document.createElement("div");
	return t.className = "me-children", t.append(...e), t;
}, fe = function(e) {
	let t = document.createElement("div");
	return t.className = "me-tpc", t.nodeObj = e, t.dataset.nodeid = "me" + e.id, t;
}, pe = function(e) {
	let t = document.createElement("div");
	return t.className = `me-main ${e}`, t;
}, me = function(e) {
	let t = e.classList;
	return t.contains(P.DOWN) ? P.DOWN : t.contains(P.LHS) ? P.LHS : P.RHS;
};
function he(e) {
	let t = document.createRange();
	t.selectNodeContents(e);
	let n = window.getSelection();
	n && (n.removeAllRanges(), n.addRange(t));
}
var ge = function(e) {
	if (!e) return;
	let t = document.createElement("div"), n = e.nodeObj, r = n.topic, i = e.text, a = _(this.nodes, i), o = getComputedStyle(e), s = a.offsetLeft - parseFloat(o.paddingLeft || "0"), c = a.offsetTop - parseFloat(o.paddingTop || "0");
	this.nodes.appendChild(t), t.id = "input-box", t.textContent = r, t.contentEditable = "plaintext-only", t.spellcheck = !1, t.style.cssText = `
  left: ${s}px;
  top: ${c}px;
  min-width:${i.offsetWidth - 8}px;
  color:${o.color};
  font-size:${o.fontSize};
  padding:${o.padding};
  margin:${o.margin}; 
  background-color:${o.backgroundColor !== "rgba(0, 0, 0, 0)" && o.backgroundColor};
  border: ${o.border};
  border-radius:${o.borderRadius}; `, this.direction === 0 && (t.style.right = "0"), i.style.opacity = "0", e.style.outline = "none", he(t), this.bus.fire("operation", {
		name: "beginEdit",
		target: e.nodeObj
	}), t.addEventListener("keydown", (e) => {
		if (e.stopPropagation(), e.isComposing) return;
		let n = e.key;
		if (n === "Enter" || n === "Tab") {
			if (e.shiftKey) return;
			e.preventDefault(), t.blur(), this.container.focus();
		} else n === "Escape" && (e.preventDefault(), t.textContent = r, t.blur(), this.container.focus());
	}), t.addEventListener("blur", () => {
		if (!t) return;
		i.style.opacity = "1", e.style.outline = "";
		let a = t.innerText?.trim() || "";
		t.remove(), a !== r && a !== "" && (n.topic = a, this.markdown ? e.text.innerHTML = this.markdown(n.topic, n) : e.text.textContent = a, this.linkDiv(), this.bus.fire("operation", {
			name: "finishEdit",
			target: n,
			origin: r
		}));
	});
}, _e = function(e) {
	let t = document.createElement("div");
	return t.className = "me-epd" + (e === !1 ? "" : " minus"), t.expanded = e !== !1, t;
}, ve = (e) => {
	let t = e.parent?.children;
	return {
		siblings: t,
		index: t?.indexOf(e) ?? 0
	};
};
function ye(e) {
	let { siblings: t, index: n } = ve(e);
	return t === void 0 ? 0 : (n === -1 || t.splice(n, 1), t.length);
}
function be(e, t, n) {
	let { siblings: r, index: i } = ve(n);
	r !== void 0 && (t === "before" ? r.splice(i, 0, e) : r.splice(i + 1, 0, e));
}
function xe(e, t) {
	let { siblings: n, index: r } = ve(e);
	n !== void 0 && (n[r] = t, t.children = [e]);
}
function Se(e, t, n) {
	if (ye(t), n.parent?.parent || (t.direction = n.direction), e === "in") n.children ? n.children.push(t) : n.children = [t];
	else {
		t.direction !== void 0 && (t.direction = n.direction);
		let { siblings: r, index: i } = ve(n);
		if (r === void 0) return;
		e === "before" ? r.splice(i, 0, t) : r.splice(i + 1, 0, t);
	}
}
//#endregion
//#region src/utils/domManipulation.ts
var Ce = function({ map: e, direction: t }, n) {
	if (t === 0) return 0;
	if (t === 1) return 1;
	if (t === 3) return 3;
	if (t === 2) return (e.querySelector(".lhs")?.childElementCount || 0) <= (e.querySelector(".rhs")?.childElementCount || 0) ? (n.direction = 0, 0) : (n.direction = 1, 1);
}, we = function(e, t, n) {
	let r = n.children[0].children[0], i = t.parentElement;
	if (i.classList.contains("me-parent")) {
		if (F(r), i.children[1]) i.nextSibling.appendChild(n);
		else {
			let t = e.createChildren([n]);
			i.appendChild(_e(!0)), i.insertAdjacentElement("afterend", t);
		}
		e.linkDiv(n.offsetParent);
	} else if (i.classList.contains("me-root")) {
		let t = Ce(e, r.nodeObj);
		t === 3 ? e.container.querySelector(".me-main.down")?.appendChild(n) : t === 0 ? e.container.querySelector(".lhs")?.appendChild(n) : e.container.querySelector(".rhs")?.appendChild(n), e.linkDiv();
	}
}, Te = function(e, t) {
	let n = e.parentNode;
	if (t === 0) {
		let e = n.parentNode.parentNode;
		e.classList.contains("me-main") || (e.previousSibling.children[1].remove(), e.remove());
	}
	n.parentNode.remove();
}, Ee = /* @__PURE__ */ t({
	addChild: () => Me,
	beginEdit: () => Ve,
	copyNodes: () => Ne,
	insertParent: () => je,
	insertSibling: () => Ae,
	moveDownNode: () => Ie,
	moveNodesAfter: () => Be,
	moveNodesBefore: () => ze,
	moveNodesIn: () => Re,
	moveUpNode: () => Fe,
	removeNodes: () => Le,
	reshapeNode: () => Oe,
	rmSubline: () => F,
	setNodeTopic: () => He
}), De = {
	before: "beforebegin",
	after: "afterend"
}, F = function(e) {
	let t = e.parentElement.parentElement.lastElementChild;
	t?.tagName === "svg" && t?.remove();
}, Oe = function(e, t) {
	let n = e.nodeObj, r = g(n);
	r.style && t.style && (t.style = Object.assign({}, r.style, t.style));
	let i = Object.assign(n, t);
	ce.call(this, e, i), this.linkDiv(), this.bus.fire("operation", {
		name: "reshapeNode",
		target: i,
		origin: r
	});
}, ke = function(e, t, n) {
	if (!t) return null;
	let r = t.nodeObj;
	r.expanded === !1 && (e.expandNode(t, !0, { silent: !0 }), t = e.findEle(r.id));
	let i = n || e.generateNewObj();
	r.children ? r.children.push(i) : r.children = [i], u(e.nodeData);
	let { grp: a, top: o } = e.createWrapper(i);
	return we(e, t, a), {
		newTop: o,
		newNodeObj: i
	};
}, Ae = function(e, t, n) {
	let r = t || this.currentNode;
	if (!r) return;
	let i = r.nodeObj;
	if (!i.parent) {
		this.addChild();
		return;
	}
	if (!i.parent?.parent && this.direction === 2) {
		let e = this.map.querySelector(".lhs")?.childElementCount || 0, t = this.map.querySelector(".rhs")?.childElementCount || 0;
		if (!e || !t) {
			this.addChild(this.findEle(i.parent.id), n);
			return;
		}
	}
	let a = n || this.generateNewObj();
	i.parent?.parent || (a.direction = +!r.closest(".me-main").classList.contains(P.LHS)), be(a, e, i), u(this.nodeData);
	let o = r.parentElement, { grp: s, top: c } = this.createWrapper(a);
	o.parentElement.insertAdjacentElement(De[e], s), this.linkDiv(s.offsetParent), n || this.editTopic(c.firstChild), this.bus.fire("operation", {
		name: "insertSibling",
		position: e,
		target: a
	}), this.selectNode(c.firstChild, !0);
}, je = function(e, t) {
	let n = e || this.currentNode;
	if (!n) return;
	F(n);
	let r = n.nodeObj;
	if (!r.parent) return;
	let i = t || this.generateNewObj();
	r.parent?.parent || (i.direction = +!n.closest(".me-main").classList.contains(P.LHS)), xe(r, i), u(this.nodeData);
	let a = n.parentElement.parentElement, { grp: o, top: s } = this.createWrapper(i, !0);
	s.appendChild(_e(!0)), a.insertAdjacentElement("afterend", o);
	let c = this.createChildren([a]);
	s.insertAdjacentElement("afterend", c), this.linkDiv(), t || this.editTopic(s.firstChild), this.bus.fire("operation", {
		name: "insertParent",
		target: i
	}), this.selectNode(s.firstChild, !0);
}, Me = function(e, t) {
	let n = e || this.currentNode;
	if (!n) return;
	let r = ke(this, n, t);
	if (!r) return;
	let { newTop: i, newNodeObj: a } = r;
	this.bus.fire("operation", {
		name: "addChild",
		target: a
	}), t || this.editTopic(i.firstChild), this.selectNode(i.firstChild, !0);
}, Ne = function(e, t) {
	let n = [];
	for (let r = 0; r < e.length; r++) {
		let i = e[r], a = g(i.nodeObj);
		f(a);
		let o = ke(this, t, a);
		if (!o) return;
		let { newNodeObj: s } = o;
		n.push(s);
	}
	this.bus.fire("operation", {
		name: "copyNodes",
		target: n
	}), this.unselectNodes(this.currentNodes), this.selectNodes(n.map((e) => this.findEle(e.id)));
}, Pe = function(e, t, n) {
	let r = t.parent?.children;
	if (r === void 0) return;
	let i = e.direction === 2 && !t.parent?.parent, a = (e) => !i || e.direction === t.direction, o, s = !1;
	for (let e of r) if (a(e)) {
		if (e === t) {
			if (n === -1) return o ? {
				to: o,
				type: "before"
			} : void 0;
			s = !0;
			continue;
		}
		if (s) return {
			to: e,
			type: "after"
		};
		o = e;
	}
}, Fe = function(e) {
	let t = e || this.currentNode;
	if (!t) return;
	let n = t.nodeObj;
	if (!n.parent) return;
	let r = Pe(this, n, -1);
	r && I([t], r.type, this.findEle(r.to.id), this);
}, Ie = function(e) {
	let t = e || this.currentNode;
	if (!t) return;
	let n = t.nodeObj;
	if (!n.parent) return;
	let r = Pe(this, n, 1);
	r && I([t], r.type, this.findEle(r.to.id), this);
}, Le = function(e) {
	if (e = b(e), e.length === 0) return;
	for (let t of e) {
		let e = t.nodeObj;
		Te(t, ye(e));
	}
	let t = e[e.length - 1];
	this.selectNode(this.findEle(t.nodeObj.parent.id)), this.linkDiv(), this.bus.fire("operation", {
		name: "removeNodes",
		target: e.map((e) => e.nodeObj)
	});
}, I = (e, t, n, r) => {
	e = b(e);
	let i = n.nodeObj;
	t === "in" && i.expanded === !1 && (r.expandNode(n, !0, { silent: !0 }), n = r.findEle(i.id), i = n.nodeObj), t === "after" && (e = e.reverse());
	let a = /* @__PURE__ */ new Set();
	for (let o of e) {
		let e = o.nodeObj;
		if (Se(t, e, i), t === "in") {
			let e = o.parentElement.parentElement, t = e.parentElement;
			we(r, n, e), a.add(t);
		} else {
			F(o);
			let e = o.parentElement.parentNode;
			a.add(e.parentElement), n.parentElement.parentNode.insertAdjacentElement(De[t], e);
		}
	}
	u(r.nodeData);
	for (let e of a) e.childElementCount === 0 && !e.classList.contains("me-main") && (e.previousSibling.children[1].remove(), e.remove());
	r.linkDiv(), r.scrollIntoView(e[e.length - 1]);
	let o = t === "before" ? "moveNodesBefore" : t === "after" ? "moveNodesAfter" : "moveNodesIn";
	r.bus.fire("operation", {
		name: o,
		target: e.map((e) => e.nodeObj),
		destination: i
	});
}, Re = function(e, t) {
	I(e, "in", t, this);
}, ze = function(e, t) {
	I(e, "before", t, this);
}, Be = function(e, t) {
	I(e, "after", t, this);
}, Ve = function(e) {
	let t = e || this.currentNode;
	t && (t.nodeObj.dangerouslySetInnerHTML || this.editTopic(t));
}, He = function(e, t) {
	e.text.textContent = t, e.nodeObj.topic = t, this.linkDiv();
}, Ue = /* @__PURE__ */ t({
	cancelFocus: () => ct,
	clearSelection: () => Ye,
	disableEdit: () => et,
	enableEdit: () => $e,
	expandNode: () => ht,
	expandNodeAll: () => gt,
	focusNode: () => st,
	getData: () => Qe,
	getDataString: () => Ze,
	initDown: () => ft,
	initLeft: () => lt,
	initRight: () => ut,
	initSide: () => dt,
	install: () => ot,
	move: () => rt,
	refresh: () => _t,
	scale: () => tt,
	scaleFit: () => nt,
	scrollIntoView: () => Ge,
	selectNode: () => Ke,
	selectNodes: () => qe,
	stringifyData: () => Xe,
	toCenter: () => at,
	unselectNodes: () => Je
});
function We(e) {
	return {
		nodeData: e.isFocusMode ? e.nodeDataBackup : e.nodeData,
		arrows: e.arrows,
		summaries: e.summaries,
		direction: e.direction,
		theme: e.theme,
		compact: e.compact,
		meta: e.meta
	};
}
var Ge = function(e, t = !1) {
	let n = this.container, r = e.getBoundingClientRect(), i = n.getBoundingClientRect();
	if (t || r.top > i.bottom - 50 || r.bottom < i.top + 50 || r.left > i.right - 50 || r.right < i.left + 50) {
		let e = r.left + r.width / 2, t = r.top + r.height / 2, n = i.left + i.width / 2, a = i.top + i.height / 2, o = e - n, s = t - a;
		this.move(-o, -s, !0);
	}
}, Ke = function(e, t, n) {
	this.clearSelection(), this.scrollIntoView(e), this.selection?.select(e), t && this.bus.fire("selectNewNode", e.nodeObj);
}, qe = function(e) {
	this.selection?.select(e);
}, Je = function(e) {
	this.selection?.deselect(e);
}, Ye = function() {
	this.unselectNodes(this.currentNodes), this.unselectSummary(), this.unselectArrow();
}, Xe = function(e) {
	return JSON.stringify(e, (e, t) => {
		if (e !== "parent" || typeof t == "string") return t;
	});
}, Ze = function() {
	return Xe(We(this));
}, Qe = function() {
	return JSON.parse(this.getDataString());
}, $e = function() {
	this.editable = !0;
}, et = function() {
	this.editable = !1;
}, tt = function(e, t = {
	x: 0,
	y: 0
}) {
	if (e < this.scaleMin && e < this.scaleVal || e > this.scaleMax && e > this.scaleVal) return;
	let n = this.container.getBoundingClientRect(), r = t.x ? t.x - n.left - n.width / 2 : 0, i = t.y ? t.y - n.top - n.height / 2 : 0, { dx: a, dy: o } = it(this), s = this.map.style.transform, { x: c, y: l } = x(s), u = c - a, d = l - o, f = this.scaleVal, p = (-r + u) * (1 - e / f), m = (-i + d) * (1 - e / f);
	this.map.style.transform = `translate3d(${c - p}px, ${l - m}px, 0) scale(${e})`, this.scaleVal = e, this.bus.fire("scale", e);
}, nt = function() {
	let e = this.nodes.offsetHeight / this.container.offsetHeight, t = this.nodes.offsetWidth / this.container.offsetWidth, n = 1 / Math.max(1, Math.max(e, t));
	this.scaleVal = n;
	let { dx: r, dy: i } = it(this, !0);
	this.map.style.transform = `translate3d(${r}px, ${i}px, 0) scale(${n})`, this.bus.fire("scale", n);
}, rt = function(e, t, n = !1) {
	let { map: r, scaleVal: i, bus: a, container: o, nodes: s } = this;
	if (n && r.style.transition === "transform 0.3s") return !1;
	let c = r.style.transform, { x: l, y: u } = x(c), d = o.getBoundingClientRect(), f = s.getBoundingClientRect(), p = (d.left + d.right) / 2, m = (d.top + d.bottom) / 2;
	return e > 0 ? e = Math.min(e, Math.max(0, p - f.left)) : e < 0 && (e = Math.max(e, Math.min(0, p - f.right))), t > 0 ? t = Math.min(t, Math.max(0, m - f.top)) : t < 0 && (t = Math.max(t, Math.min(0, m - f.bottom))), e === 0 && t === 0 ? !1 : (l += e, u += t, n && (r.style.transition = "transform 0.3s", setTimeout(() => {
		r.style.transition = "none";
	}, 300)), r.style.transform = `translate3d(${l}px, ${u}px, 0) scale(${i})`, a.fire("move", {
		dx: e,
		dy: t
	}), !0);
}, it = (e, t = !1) => {
	let { container: n, map: r, nodes: i } = e, a, o;
	if (e.alignment === "nodes" || t || e.direction === 3) a = (n.offsetWidth - i.offsetWidth) / 2, o = (n.offsetHeight - i.offsetHeight) / 2, r.style.transformOrigin = "50% 50%";
	else {
		let e = r.querySelector(".me-root"), t = e.offsetTop, i = e.offsetLeft, s = e.offsetWidth, c = e.offsetHeight;
		a = n.offsetWidth / 2 - i - s / 2, o = n.offsetHeight / 2 - t - c / 2, r.style.transformOrigin = `${i + s / 2}px 50%`;
	}
	return {
		dx: a,
		dy: o
	};
}, at = function() {
	let { map: e, container: t } = this, { dx: n, dy: r } = it(this);
	t.scrollTop = 0, t.scrollLeft = 0, e.style.transform = `translate3d(${n}px, ${r}px, 0) scale(${this.scaleVal})`;
}, ot = function(e) {
	e(this);
}, st = function(e) {
	e.nodeObj.parent && (this.clearSelection(), this.tempDirection === null && (this.tempDirection = this.direction), this.isFocusMode ||= (this.nodeDataBackup = this.nodeData, !0), this.nodeData = e.nodeObj, this.initRight(), this.clearHistory?.(), this.toCenter());
}, ct = function() {
	this.isFocusMode = !1, this.tempDirection !== null && (this.nodeData = this.nodeDataBackup, this.direction = this.tempDirection, this.tempDirection = null, this.refresh(), this.clearHistory?.(), this.toCenter());
}, lt = function() {
	this.direction = 0, this.refresh(), this.toCenter(), this.bus.fire("changeDirection", this.direction);
}, ut = function() {
	this.direction = 1, this.refresh(), this.toCenter(), this.bus.fire("changeDirection", this.direction);
}, dt = function() {
	this.direction = 2, this.refresh(), this.toCenter(), this.bus.fire("changeDirection", this.direction);
}, ft = function() {
	this.direction = 3, this.refresh(), this.toCenter(), this.bus.fire("changeDirection", this.direction);
}, pt = (e) => e.expanded !== !1 || (e.children ?? []).some(pt), mt = (e, t, n) => {
	if (e.expanded !== !1 !== t) return !0;
	let r = e.children ?? [];
	if (!r.length) return !1;
	if (n !== void 0 && n <= 0) return r.some(pt);
	let i = n === void 0 ? void 0 : n - 1;
	return r.some((e) => mt(e, t, i));
}, ht = function(e, t, n) {
	let r = e.nodeObj;
	if (!r.children?.length) return;
	let i = r.expanded !== !1, a = typeof t == "boolean" ? t : !i;
	if (a === i) return;
	r.expanded = a;
	let o = e.getBoundingClientRect(), s = {
		x: o.left,
		y: o.top
	}, c = e.parentNode, l = c.children[1];
	if (l.expanded = r.expanded, l.className = "me-epd" + (r.expanded ? " minus" : ""), F(e), r.expanded) {
		let e = this.createChildren(r.children.map((e) => this.createWrapper(e).grp));
		c.parentNode.appendChild(e);
	} else c.parentNode.children[1].remove();
	this.linkDiv(e.closest(".me-main > .me-wrapper"));
	let u = e.getBoundingClientRect(), d = {
		x: u.left,
		y: u.top
	}, f = s.x - d.x, p = s.y - d.y;
	this.move(f, p), this.bus.fire("operation", {
		name: a ? "expandNode" : "collapseNode",
		target: r,
		silent: n?.silent
	});
}, gt = function(e, t, n) {
	let r = e.nodeObj, i = t ?? !r.expanded;
	if (!mt(r, i)) return;
	let a = e.getBoundingClientRect(), o = {
		x: a.left,
		y: a.top
	};
	d(r, i), this.refresh();
	let s = this.findEle(r.id).getBoundingClientRect(), c = {
		x: s.left,
		y: s.top
	}, l = o.x - c.x, u = o.y - c.y;
	this.move(l, u), this.bus.fire("operation", {
		name: i ? "expandNode" : "collapseNode",
		target: r,
		recursive: !0,
		silent: n?.silent
	});
}, _t = function(e) {
	this.clearSelection(), e && (e = JSON.parse(JSON.stringify(e)), this.nodeData = e.nodeData, this.arrows = e.arrows || [], this.summaries = e.summaries || [], e.meta && (this.meta = e.meta), this.isFocusMode = !1, this.nodeDataBackup = this.nodeData, this.bus.fire("refresh")), u(this.nodeData), this.layout(), this.linkDiv();
}, vt = "MIND-ELIXIR-WAIT-COPY", yt = 40, bt = 10, xt = ({ deltaMode: e, deltaY: t, viewportHeight: n }) => e === WheelEvent.DOM_DELTA_LINE ? t * yt : e === WheelEvent.DOM_DELTA_PAGE ? t * n : t, St = ({ deltaMode: e, deltaY: t, scaleSensitivity: n, viewportHeight: r }) => {
	let i = -xt({
		deltaMode: e,
		deltaY: t,
		viewportHeight: r
	}) / bt * n;
	return Math.max(-n, Math.min(n, i));
}, Ct = (e, t, n) => {
	t !== 0 && e.scale(e.scaleVal + t, n);
}, L = (e) => {
	let t = e.currentNodes;
	return t && t.length > 0 ? t[t.length - 1] : null;
}, wt = (e, t) => {
	let n = e.map.querySelectorAll(`.${t}>.me-wrapper>.me-parent>.me-tpc`);
	n.length !== 0 && e.selectNode(n[Math.ceil(n.length / 2) - 1]);
}, Tt = (e) => {
	e.selectNode(e.map.querySelector(".me-root>.me-tpc"));
}, Et = function(e, t) {
	let n = t.parentElement.parentElement.parentElement.previousSibling;
	if (n) {
		let t = n.firstChild;
		e.selectNode(t);
	}
}, Dt = function(e, t) {
	let n = t.parentElement.nextSibling;
	if (n && n.firstChild) {
		let t = n.firstChild.firstChild.firstChild;
		e.selectNode(t);
	}
}, Ot = function(e, t) {
	let n = L(e);
	if (!n) return;
	let r = n.nodeObj;
	r.parent ? me(n.closest(".me-main")) === t ? Dt(e, n) : r.parent?.parent ? Et(e, n) : Tt(e) : wt(e, t);
}, kt = (e, t) => {
	let n = t === "next" ? "nextElementSibling" : "previousElementSibling", r = t === "next" ? "firstElementChild" : "lastElementChild", i = e;
	for (; i;) {
		let e = i[n];
		if (e) {
			let t = e.children[1];
			return ((t ? t[r] : null) || e).firstElementChild?.firstElementChild || null;
		}
		let t = i.parentElement;
		if (!t || t.classList.contains("me-main")) return null;
		i = t.parentElement;
	}
	return null;
}, R = function(e, t) {
	let n = L(e);
	if (!n || !n.nodeObj.parent) return;
	let r = t + "Sibling", i = n.parentElement.parentElement[r];
	if (i) e.selectNode(i.firstChild.firstChild);
	else {
		let r = kt(n.parentElement.parentElement, t);
		if (r) {
			e.selectNode(r);
			return;
		}
		e.currentNodes && e.currentNodes.length !== 1 && e.selectNode(n);
	}
}, At = function(e, t) {
	let n = t.nodeObj;
	n.parent && (n.parent.parent ? Et(e, t) : Tt(e));
}, jt = function(e, t) {
	if (t.nodeObj.parent) Dt(e, t);
	else {
		let t = e.map.querySelectorAll(".down>.me-wrapper>.me-parent>.me-tpc");
		if (t.length === 0) return;
		e.selectNode(t[Math.ceil(t.length / 2) - 1]);
	}
}, Mt = function(e, t, n) {
	Ct(e, t === "in" ? e.scaleSensitivity : -e.scaleSensitivity, n);
}, Nt = (e, t) => {
	Ct(e, St({
		deltaMode: t.deltaMode,
		deltaY: t.deltaY,
		scaleSensitivity: e.scaleSensitivity,
		viewportHeight: e.container.clientHeight || window.innerHeight
	}), {
		x: t.clientX,
		y: t.clientY
	});
};
function Pt(e, t) {
	t = t === !0 ? {} : t;
	let n = () => {
		e.currentArrow ? e.removeArrow() : e.currentSummary ? e.removeSummary(e.currentSummary.summaryObj.id) : e.currentNodes && e.removeNodes(e.currentNodes);
	}, r = !1, i = null, a = () => {
		r = !1, i &&= (clearTimeout(i), null), e.container.removeEventListener("keydown", o);
	}, o = (t) => {
		if ([
			"Control",
			"Meta",
			"Shift",
			"Alt"
		].includes(t.key)) return;
		let n = e.nodeData;
		if (!n.children?.length) {
			a();
			return;
		}
		let r = !0, i = null, o;
		if (t.key === "0") {
			i = !1;
			for (let e of n.children) d(e, !1);
		} else if (t.key === "=") {
			i = !0;
			for (let e of n.children) d(e, !0);
		} else if ([
			"1",
			"2",
			"3",
			"4",
			"5",
			"6",
			"7",
			"8",
			"9"
		].includes(t.key)) {
			i = !0, o = Number(t.key) - 1;
			for (let e of n.children) d(e, !0, o);
		} else r = !1;
		r && (e.refresh(), e.toCenter(), i !== null && e.bus.fire("operation", {
			name: i ? "expandNode" : "collapseNode",
			target: n,
			recursive: !0,
			level: o
		})), a();
	}, s = {
		Enter: (t) => {
			t.shiftKey ? e.insertSibling("before") : t.ctrlKey || t.metaKey ? e.insertParent() : e.insertSibling("after");
		},
		Tab: () => {
			e.addChild();
		},
		F1: () => {
			e.toCenter();
		},
		F2: () => {
			e.currentSummary ? e.editSummary(e.currentSummary) : e.currentArrow ? e.editArrowLabel(e.currentArrow) : e.beginEdit();
		},
		ArrowUp: (t) => {
			if (t.altKey) e.moveUpNode();
			else if (t.metaKey || t.ctrlKey) return e.initSide();
			else if (e.direction === 3) {
				let t = L(e);
				t && At(e, t);
			} else R(e, "previous");
		},
		ArrowDown: (t) => {
			if (t.altKey) e.moveDownNode();
			else if (e.direction === 3) {
				let t = L(e);
				t && jt(e, t);
			} else R(e, "next");
		},
		ArrowLeft: (t) => {
			if (t.metaKey || t.ctrlKey) return e.initLeft();
			e.direction === 3 ? R(e, "previous") : Ot(e, P.LHS);
		},
		ArrowRight: (t) => {
			if (t.metaKey || t.ctrlKey) return e.initRight();
			e.direction === 3 ? R(e, "next") : Ot(e, P.RHS);
		},
		PageUp: () => e.moveUpNode(),
		PageDown: () => {
			e.moveDownNode();
		},
		"=": (t) => {
			(t.metaKey || t.ctrlKey) && Mt(e, "in");
		},
		"-": (t) => {
			(t.metaKey || t.ctrlKey) && Mt(e, "out");
		},
		0: (t) => {
			if (t.metaKey || t.ctrlKey) {
				if (r) return;
				e.scale(1);
			}
		},
		k: (t) => {
			(t.metaKey || t.ctrlKey) && (a(), r = !0, i = window.setTimeout(() => {
				i = null, a();
			}, 2e3), e.container.addEventListener("keydown", o));
		},
		Delete: n,
		Backspace: n,
		...t
	};
	e.container.onkeydown = (t) => {
		if ((t.ctrlKey || t.metaKey) && [
			"c",
			"v",
			"x"
		].includes(t.key) || t.preventDefault(), !e.editable) return;
		let n = s[t.key];
		n && n(t);
	};
	let c = (t) => {
		if (t.target instanceof HTMLElement && t.target.id === "input-box" || e.currentNodes.length === 0) return !1;
		if (t.clipboardData) {
			let n = Xe({
				magic: vt,
				data: b(e.currentNodes).map((e) => e.nodeObj)
			});
			return t.clipboardData.setData("text/plain", n), t.preventDefault(), !0;
		}
		return !1;
	};
	e.container.addEventListener("copy", c), e.container.addEventListener("cut", (e) => {
		c(e) && n();
	}), e.container.addEventListener("paste", (t) => {
		let n = t.clipboardData?.getData("text/plain");
		if (n) try {
			let r = JSON.parse(n);
			if (r && r.magic === vt && Array.isArray(r.data)) {
				let n = r.data, i = n.map((e) => ({ nodeObj: e }));
				n.length > 0 && e.currentNode && (e.copyNodes(i, e.currentNode), t.preventDefault());
				return;
			}
		} catch {}
		e.pasteHandler && e.pasteHandler(t);
	});
}
//#endregion
//#region src/mouse.ts
function Ft(e) {
	let { panHelper: t, container: n } = e, r = null, i = 0;
	e.spacePressed = !1;
	let a = {
		lastTap: 0,
		lastTapTarget: null,
		DOUBLE_CLICK_THRESHOLD: 300,
		detect(e, t) {
			if (e.button !== 0) {
				this.clear();
				return;
			}
			let n = (/* @__PURE__ */ new Date()).getTime(), r = n - this.lastTap, i = r < this.DOUBLE_CLICK_THRESHOLD && r > 0 && this.lastTapTarget === e.target;
			this.lastTap = n, this.lastTapTarget = e.target, i && t(e);
		},
		clear() {
			this.lastTap = 0, this.lastTapTarget = null;
		}
	}, o = {
		Idle: 0,
		Pinch: 1,
		DragWait: 2,
		Drag: 3,
		Pan: 4,
		BoxSelect: 5
	};
	e.ptState = o.Idle;
	let s = {
		lastDistance: null,
		activePointers: /* @__PURE__ */ new Map(),
		handlePointerDown(e) {
			if (e.pointerType !== "touch") return !1;
			if (this.activePointers.set(e.pointerId, {
				x: e.clientX,
				y: e.clientY
			}), this.activePointers.size >= 2) {
				let [e, t] = Array.from(this.activePointers.values());
				return this.lastDistance = C(e, t), !0;
			}
			return !1;
		},
		handlePointerMove(t) {
			if (t.pointerType !== "touch" || !this.activePointers.has(t.pointerId)) return !1;
			if (this.activePointers.set(t.pointerId, {
				x: t.clientX,
				y: t.clientY
			}), this.activePointers.size >= 2) {
				let [t, n] = Array.from(this.activePointers.values()), r = C(t, n);
				if (this.lastDistance !== null && this.lastDistance > 0) {
					let i = r / this.lastDistance;
					e.scale(e.scaleVal * i, {
						x: (t.x + n.x) / 2,
						y: (t.y + n.y) / 2
					});
				}
				return this.lastDistance = r, !0;
			}
			return !1;
		},
		handlePointerUp(e) {
			e.pointerType === "touch" && (this.activePointers.delete(e.pointerId), this.activePointers.size < 2 && (this.lastDistance = null));
		},
		clear() {
			this.activePointers.clear(), this.lastDistance = null;
		}
	}, c = k(e), l = {
		timer: null,
		startPos: null,
		pointerId: null,
		DURATION: 500,
		MOVE_THRESHOLD: 10,
		clear() {
			this.timer !== null && (clearTimeout(this.timer), this.timer = null, this.startPos = null, this.pointerId = null);
		},
		start(e, t) {
			this.timer = window.setTimeout(() => {
				t(e), this.timer = null, this.startPos = null, this.pointerId = null;
			}, this.DURATION), this.startPos = {
				x: e.clientX,
				y: e.clientY
			}, this.pointerId = e.pointerId;
		},
		handleMove(e) {
			if (this.timer !== null && this.startPos !== null && e.pointerId === this.pointerId) {
				let t = e.clientX - this.startPos.x, n = e.clientY - this.startPos.y;
				Math.sqrt(t * t + n * n) > this.MOVE_THRESHOLD && this.clear();
			}
		}
	}, u = (t, n) => {
		if (t.closest("#input-box")) return !1;
		let r = t.closest(".svg-label"), i = t.closest(".topiclinks, .summary"), a = r ? {
			type: r.dataset.type,
			element: document.getElementById(r.dataset.svgId)
		} : i ? {
			type: i.classList.contains("topiclinks") ? "arrow" : "summary",
			element: t.closest("g")
		} : null;
		if (!a?.type || !a?.element) return !1;
		let { type: o, element: s } = a;
		return e.clearSelection(), o === "arrow" ? n ? e.editArrowLabel(s) : e.selectArrow(s) : n ? e.editSummary(s) : e.selectSummary(s), !0;
	}, d = (n) => {
		if (n.pointerType === "mouse" && n.button !== 0) return;
		if (e.helper1?.moved) {
			e.helper1.clear();
			return;
		}
		if (e.helper2?.moved) {
			e.helper2.clear();
			return;
		}
		if (t.moved) {
			t.clear();
			return;
		}
		if (c?.isDragging) return;
		let r = n.target;
		r.classList.contains("me-epd") && (n.ctrlKey || n.metaKey ? e.expandNodeAll(r.previousSibling) : e.expandNode(r.previousSibling));
	}, f = (t) => {
		if (!e.editable) return;
		let n = t.target;
		if (y(n)) {
			if (e.selectNode(n), n.image) {
				let e = n.text.getBoundingClientRect(), { clientX: r, clientY: i } = t;
				if (r < e.left || r > e.right || i < e.top || i > e.bottom) return;
			}
			e.beginEdit(n);
			return;
		}
		u(n, !0);
	}, p = (a) => {
		if (a.pointerType === "touch" && s.handlePointerDown(a)) {
			e.ptState = o.Pinch, l.clear(), t.clear(), (c.isDragging || c.pointerId !== null) && ne(e, c);
			return;
		}
		if (e.ptState === o.Pinch) return;
		let d = a.target, f = a.button === e.mouseSelectionButton;
		if (d === n && (a.pointerType === "touch" || e.mouseSelectionButton === 2 && a.button === 0 && a.pointerType === "mouse") && e.clearSelection(), e.editable && !e.spacePressed && d === n && f && a.pointerType === "mouse") {
			if (!a.ctrlKey && !a.metaKey && e.clearSelection(), i = 0, e.ptState = o.BoxSelect, !e.selection?.start(a)) {
				e.ptState = o.Idle;
				return;
			}
			return;
		}
		let p = y(d);
		if (e.editable && p && d.nodeObj.parent && a.button === 0 && a.pointerType === "mouse" || (t.handlePointerDown(a), t.mousedown && (e.ptState = o.Pan)), a.button === 0 || a.pointerType === "touch") if (p) {
			e.selection?.cancel();
			let t = e.currentNodes || [];
			if (a.ctrlKey || a.metaKey || e.mobileMultiSelect ? t.includes(d) ? r = d : ((e.currentArrow || e.currentSummary) && e.clearSelection(), e.selection?.select(d)) : t.includes(d) || e.selectNode(d), !e.editable) return;
			a.pointerType === "touch" ? (e.ptState = o.DragWait, l.start(a, (t) => {
				j(e, c, t, !0) && (e.ptState = o.Drag, d.setPointerCapture(t.pointerId));
			})) : j(e, c, a, !1) && (e.ptState = o.Drag, d.setPointerCapture(a.pointerId));
		} else u(d, !1);
	}, m = (n) => {
		switch (e.ptState) {
			case o.Pinch:
				s.handlePointerMove(n);
				break;
			case o.BoxSelect:
				n.pointerType === "mouse" && e.selection?.move(n);
				break;
			case o.DragWait:
				l.handleMove(n), l.timer === null && (e.ptState = o.Pan, t.handlePointerMove(n));
				break;
			case o.Drag:
				ee(e, c, n);
				break;
			case o.Pan: t.handlePointerMove(n);
		}
	}, h = (e) => {
		e.preventDefault(), e.stopImmediatePropagation(), window.removeEventListener("contextmenu", h, !0);
	}, g = () => {
		i = Date.now() + 500, window.addEventListener("contextmenu", h, {
			capture: !0,
			once: !0
		}), window.setTimeout(() => window.removeEventListener("contextmenu", h, !0), 500);
	}, _ = (n) => {
		n.pointerType === "touch" && s.handlePointerUp(n);
		let i = c.isDragging, u = t.moved;
		switch (e.ptState) {
			case o.BoxSelect:
				(e.selection?.stop(n) ?? !1) && n.button === 2 && n.pointerType === "mouse" && g();
				break;
			case o.DragWait:
				l.clear(), t.handlePointerUp(n);
				break;
			case o.Drag:
				te(e, c, n), t.handlePointerUp(n);
				break;
			case o.Pan: t.handlePointerUp(n), t.moved && n.button === 2 && n.pointerType === "mouse" && (window.addEventListener("contextmenu", h, {
				capture: !0,
				once: !0
			}), setTimeout(() => window.removeEventListener("contextmenu", h, !0), 300));
		}
		a.detect(n, f), (e.ptState !== o.Pinch || s.activePointers.size < 2) && (e.ptState = o.Idle), r &&= (!i && !u && e.selection?.deselect(r), null);
	}, v = () => {
		let n = e.ptState === o.BoxSelect;
		s.clear(), n && e.selection?.cancel(), l.clear(), t.clear(), a.clear(), i = 0, (c.isDragging || c.pointerId !== null) && ne(e, c), e.ptState = o.Idle, r = null;
	};
	return S([
		{
			dom: n,
			evt: "pointerdown",
			func: p
		},
		{
			dom: n,
			evt: "pointermove",
			func: m
		},
		{
			dom: n,
			evt: "pointerup",
			func: _
		},
		{
			dom: n,
			evt: "pointercancel",
			func: v
		},
		{
			dom: n,
			evt: "click",
			func: d
		},
		{
			dom: n,
			evt: "contextmenu",
			func: (t) => {
				t.preventDefault(), t.button === 2 && e.editable && setTimeout(() => {
					if (e.panHelper.moved || Date.now() < i || e.ptState !== o.Idle && e.ptState !== o.Pan) return;
					let n = t.target;
					y(n) && !n.classList.contains("selected") && e.selectNode(n), e.bus.fire("showContextMenu", t);
				}, 200);
			}
		},
		{
			dom: n,
			evt: "wheel",
			func: typeof e.handleWheel == "function" ? e.handleWheel : (t) => {
				if (t.ctrlKey || t.metaKey) return t.stopPropagation(), t.preventDefault(), Nt(e, t);
				(t.shiftKey ? e.move(-t.deltaY, 0) : e.move(-t.deltaX, -t.deltaY)) && (t.stopPropagation(), t.preventDefault());
			}
		},
		{
			dom: n,
			evt: "blur",
			func: v
		},
		{
			dom: n,
			evt: "keydown",
			func: (t) => {
				t.code === "Space" && (e.spacePressed = !0, e.container.classList.add("space-pressed"));
			}
		},
		{
			dom: n,
			evt: "keyup",
			func: (t) => {
				t.code === "Space" && (e.spacePressed = !1, e.container.classList.remove("space-pressed"));
			}
		}
	]);
}
//#endregion
//#region src/utils/pubsub.ts
function It() {
	return {
		handlers: {},
		addListener: function(e, t) {
			this.handlers[e] === void 0 && (this.handlers[e] = []), this.handlers[e].push(t);
		},
		fire: function(e, ...t) {
			if (this.handlers[e] instanceof Array) {
				let n = this.handlers[e];
				for (let e = 0; e < n.length; e++) n[e](...t);
			}
		},
		removeListener: function(e, t) {
			if (!this.handlers[e]) return;
			let n = this.handlers[e];
			if (!t) n.length = 0;
			else if (n.length) for (let e = n.length - 1; e >= 0; e--) n[e] === t && n.splice(e, 1);
		}
	};
}
//#endregion
//#region src/utils/svg.ts
var z = "http://www.w3.org/2000/svg", B = function(e) {
	let t = e.clientWidth, n = e.clientHeight, r = e.dataset, i = Number(r.x), a = Number(r.y), o = r.anchor, s = i;
	o === "middle" ? s = i - t / 2 : o === "end" && (s = i - t), e.style.left = `${s}px`, e.style.top = `${a - n / 2}px`, e.style.visibility = "visible";
}, Lt = function(e, t, n, r) {
	let { anchor: i = "middle", color: a, dataType: o, svgId: s } = r, c = document.createElement("div");
	return c.className = "svg-label", c.style.color = a || "#666", c.id = "label-" + s, c.innerHTML = e, c.dataset.type = o, c.dataset.svgId = s, c.dataset.x = t.toString(), c.dataset.y = n.toString(), c.dataset.anchor = i, c;
}, Rt = function(e, t, n) {
	let r = document.createElementNS(z, "path");
	return v(r, {
		d: e,
		stroke: t || "#666",
		fill: "none",
		"stroke-width": n
	}), r;
}, V = function(e) {
	let t = document.createElementNS(z, "svg");
	return t.setAttribute("class", e), t.setAttribute("overflow", "visible"), t;
}, zt = function() {
	let e = document.createElementNS(z, "line");
	return e.setAttribute("stroke", "#4dc4ff"), e.setAttribute("fill", "none"), e.setAttribute("stroke-width", "2"), e.setAttribute("opacity", "0.45"), e;
}, Bt = function(e, t, n, r) {
	let i = document.createElementNS(z, "g");
	return [
		{
			name: "line",
			d: e
		},
		{
			name: "arrow1",
			d: t
		},
		{
			name: "arrow2",
			d: n
		}
	].forEach((e, t) => {
		let n = e.d, a = document.createElementNS(z, "path"), o = {
			d: n,
			stroke: r?.stroke || "rgb(227, 125, 116)",
			fill: "none",
			"stroke-width": String(r?.strokeWidth || "2")
		};
		r?.opacity !== void 0 && (o.opacity = String(r.opacity)), v(a, o), t === 0 && a.setAttribute("stroke-dasharray", r?.strokeDasharray || "8,2");
		let s = document.createElementNS(z, "path");
		v(s, {
			d: n,
			stroke: "transparent",
			fill: "none",
			"stroke-width": "15"
		}), i.appendChild(s), i.appendChild(a), i[e.name] = a;
	}), i;
}, Vt = function(e, t, n) {
	if (!t) return;
	let r = n.label;
	t.style.opacity = "0";
	let i = t.cloneNode(!0);
	e.nodes.appendChild(i), i.id = "input-box", i.textContent = r, i.contentEditable = "plaintext-only", i.spellcheck = !1, i.style.cssText = `
    left:${t.style.left};
    top:${t.style.top}; 
    max-width: 200px;
  `, he(i), e.scrollIntoView(i), i.addEventListener("keydown", (t) => {
		if (t.stopPropagation(), t.isComposing) return;
		let n = t.key;
		if (n === "Enter" || n === "Tab") {
			if (t.shiftKey) return;
			t.preventDefault(), i.blur(), e.container.focus();
		}
	}), i.addEventListener("blur", () => {
		if (!i) return;
		let a = i.innerText?.trim() || "";
		n.label = a === "" ? r : a, t.style.opacity = "1", i.remove(), a !== r && (e.markdown ? t.innerHTML = e.markdown(n.label, n) : t.textContent = n.label, B(t), "parent" in n ? (e.renderSummary(), e.bus.fire("operation", {
			name: "finishEditSummary",
			target: n
		})) : e.bus.fire("operation", {
			name: "finishEditArrowLabel",
			target: n
		}));
	});
}, Ht = (e, t, n) => {
	let r = e[e.length - 1];
	r && r.color === n ? r.d += " " + t : e.push({
		d: t,
		color: n
	});
}, Ut = function(e) {
	let t = this.map.querySelector(".me-root"), n = t.offsetTop, r = t.offsetLeft, i = t.offsetWidth, a = t.offsetHeight, o = this.nodes.offsetHeight, s = this.nodes.offsetWidth, c = this.map.querySelectorAll(".me-main > .me-wrapper");
	this.lines.innerHTML = "";
	let l = [];
	for (let t = 0; t < c.length; t++) {
		let n = c[t];
		if (e && e !== n) {
			l.push(null);
			continue;
		}
		let r = V("subLines"), i = n.lastChild;
		i.tagName === "svg" && i.remove(), n.appendChild(r), l.push(r);
	}
	let u = [], d = this.theme.palette;
	for (let e = 0; e < c.length; e++) {
		let t = c[e], f = t.querySelector(".me-tpc"), { offsetLeft: p, offsetTop: m } = _(this.nodes, f), h = f.offsetWidth, g = f.offsetHeight, v = me(t.parentNode), y = f.nodeObj.branchColor || d[e % d.length], b = this.generateMainBranch({
			pT: n,
			pL: r,
			pW: i,
			pH: a,
			cT: m,
			cL: p,
			cW: h,
			cH: g,
			direction: v,
			containerHeight: o,
			containerWidth: s
		}), x = null;
		l[e] && (x = [], Wt(this, x, y, t, v, !0)), u.push({
			el: t,
			tpc: f,
			svg: l[e],
			d: b,
			branchColor: y,
			subPaths: x
		});
	}
	let f = document.createDocumentFragment();
	for (let e of u) {
		if (e.tpc.style.borderColor = e.branchColor, f.appendChild(Rt(e.d, e.branchColor, "3")), !e.svg || !e.subPaths) continue;
		let t = document.createDocumentFragment();
		for (let n of e.subPaths) t.appendChild(Rt(n.d, n.color, "2"));
		e.svg.appendChild(t);
	}
	this.lines.appendChild(f), this.labelContainer.innerHTML = "", this.renderArrow(), this.renderSummary(), this.bus.fire("linkDiv");
}, Wt = function(e, t, n, r, i, a) {
	let o = r.firstChild, s = r.children[1].children;
	if (s.length === 0) return;
	let c = o.offsetTop, l = o.offsetLeft, u = o.offsetWidth, d = o.offsetHeight;
	for (let r = 0; r < s.length; r++) {
		let o = s[r], f = o.firstChild, p = f.offsetTop, m = f.offsetLeft, h = f.offsetWidth, g = f.offsetHeight, _ = f.firstChild.nodeObj.branchColor || n;
		Ht(t, e.generateSubBranch({
			pT: c,
			pL: l,
			pW: u,
			pH: d,
			cT: p,
			cL: m,
			cW: h,
			cH: g,
			direction: i,
			isFirst: a
		}), _);
		let v = f.children[1];
		if (v) {
			if (!v.expanded) continue;
		} else continue;
		Wt(e, t, _, o, i);
	}
}, Gt = {
	addChild: "Add child",
	addParent: "Add parent",
	addSibling: "Add sibling",
	removeNode: "Remove node",
	focus: "Focus Mode",
	cancelFocus: "Cancel Focus Mode",
	moveUp: "Move up",
	moveDown: "Move down",
	link: "Link",
	linkBidirectional: "Bidirectional Link",
	clickTips: "Please click the target node",
	summary: "Summary"
};
//#endregion
//#region src/plugin/contextMenu.ts
function Kt(e, t) {
	let n = {
		focus: !0,
		link: !0,
		locale: Gt
	};
	t = t === !0 ? n : Object.assign(n, t);
	let r = (e) => {
		let t = document.createElement("div");
		return t.innerText = e, t.className = "tips", t;
	}, i = (e, t, n) => {
		let r = document.createElement("li");
		return r.id = e, r.innerHTML = `<span>${c(t)}</span><span ${n ? "class=\"key\"" : ""}>${c(n)}</span>`, r;
	}, a = t.locale, o = i("cm-add_child", a.addChild, "Tab"), s = i("cm-add_parent", a.addParent, "Ctrl + Enter"), l = i("cm-add_sibling", a.addSibling, "Enter"), u = i("cm-remove_child", a.removeNode, "Delete"), d = i("cm-fucus", a.focus, ""), f = i("cm-unfucus", a.cancelFocus, ""), p = i("cm-up", a.moveUp, "PgUp"), m = i("cm-down", a.moveDown, "Pgdn"), h = i("cm-link", a.link, ""), g = i("cm-link-bidirectional", a.linkBidirectional, ""), _ = i("cm-summary", a.summary, ""), v = document.createElement("ul");
	if (v.className = "menu-list", v.appendChild(o), v.appendChild(s), v.appendChild(l), v.appendChild(u), t.focus && (v.appendChild(d), v.appendChild(f)), v.appendChild(p), v.appendChild(m), v.appendChild(_), t.link && (v.appendChild(h), v.appendChild(g)), t && t.extend) for (let e = 0; e < t.extend.length; e++) {
		let n = t.extend[e], r = i(n.name, n.name, n.key || "");
		v.appendChild(r), r.onclick = (e) => {
			n.onclick(e);
		};
	}
	let b = document.createElement("div");
	b.className = "context-menu", b.appendChild(v), b.hidden = !0, e.container.append(b);
	let x = !0;
	e.bus.addListener("showContextMenu", (e) => {
		let t = e.target;
		if (y(t)) {
			x = !!t.parentElement.classList.contains("me-root"), x ? (d.className = "disabled", p.className = "disabled", m.className = "disabled", s.className = "disabled", l.className = "disabled", u.className = "disabled") : (d.className = "", p.className = "", m.className = "", s.className = "", l.className = "", u.className = ""), b.hidden = !1, v.style.top = "", v.style.bottom = "", v.style.left = "", v.style.right = "";
			let n = v.offsetHeight, r = v.offsetWidth, i = v.getBoundingClientRect(), a = e.clientY - i.top, o = e.clientX - i.left;
			n + a > window.innerHeight ? (v.style.top = "", v.style.bottom = "0px") : (v.style.bottom = "", v.style.top = a + 15 + "px"), r + o > window.innerWidth ? (v.style.left = "", v.style.right = "0px") : (v.style.right = "", v.style.left = o + 10 + "px");
		}
	}), b.onclick = (e) => {
		e.target === b && (b.hidden = !0);
	}, o.onclick = () => {
		e.addChild(), b.hidden = !0;
	}, s.onclick = () => {
		e.insertParent(), b.hidden = !0;
	}, l.onclick = () => {
		x || (e.insertSibling("after"), b.hidden = !0);
	}, u.onclick = () => {
		x || (e.removeNodes(e.currentNodes || []), b.hidden = !0);
	}, d.onclick = () => {
		x || (e.focusNode(e.currentNode), b.hidden = !0);
	}, f.onclick = () => {
		e.cancelFocus(), b.hidden = !0;
	}, p.onclick = () => {
		x || (e.moveUpNode(), b.hidden = !0);
	}, m.onclick = () => {
		x || (e.moveDownNode(), b.hidden = !0);
	};
	let S = (t) => {
		b.hidden = !0;
		let n = e.currentNode, i = r(a.clickTips);
		e.container.appendChild(i), e.map.addEventListener("click", (r) => {
			r.preventDefault(), i.remove();
			let a = r.target;
			(a.parentElement.classList.contains("me-parent") || a.parentElement.classList.contains("me-root")) && e.createArrow(n, a, t);
		}, { once: !0 });
	};
	return h.onclick = () => S(), g.onclick = () => S({ bidirectional: !0 }), _.onclick = () => {
		b.hidden = !0, e.createSummary(), e.unselectNodes(e.currentNodes);
	}, () => {
		o.onclick = null, s.onclick = null, l.onclick = null, u.onclick = null, d.onclick = null, f.onclick = null, p.onclick = null, m.onclick = null, h.onclick = null, _.onclick = null, b.onclick = null, e.container.oncontextmenu = null;
	};
}
//#endregion
//#region src/utils/treePatch.ts
var qt = [
	"topic",
	"style",
	"tags",
	"icons",
	"hyperLink",
	"expanded",
	"image",
	"branchColor",
	"dangerouslySetInnerHTML",
	"note",
	"metadata",
	"direction"
], Jt = /* @__PURE__ */ new Set([
	"topic",
	"style",
	"tags",
	"icons",
	"hyperLink",
	"expanded",
	"image",
	"branchColor",
	"dangerouslySetInnerHTML"
]), Yt = (e) => e, Xt = (e, t) => {
	let n = [[
		e,
		null,
		0
	]];
	for (; n.length;) {
		let [e, r, i] = n.pop();
		t.set(e.id, {
			node: e,
			parentId: r,
			index: i
		});
		let a = e.children;
		if (a) for (let t = a.length - 1; t >= 0; t--) n.push([
			a[t],
			e.id,
			t
		]);
	}
}, Zt = (e) => {
	let t = [], n = [e];
	for (; n.length;) {
		let e = n.pop();
		t.push(e.id);
		let r = e.children;
		if (r) for (let e = r.length - 1; e >= 0; e--) n.push(r[e]);
	}
	return t;
}, Qt = (e, t) => {
	if (e === t) return !0;
	if (e === null || t === null || e === void 0 || t === void 0 || typeof e != "object" || typeof t != "object") return !1;
	try {
		return JSON.stringify(e) === JSON.stringify(t);
	} catch {
		return !1;
	}
}, $t = (e) => {
	let t = {};
	for (let n in e) {
		let r = e[n];
		t[n] = r === void 0 ? void 0 : g(r);
	}
	return t;
};
function en(e, t, n) {
	if (e === t) return [];
	if (e.id !== t.id) return [{ type: "resync" }];
	let r = /* @__PURE__ */ new Map(), i = /* @__PURE__ */ new Map();
	Xt(e, r), Xt(t, i);
	for (let [t, n] of i) {
		let i = r.get(t);
		if (!(!i || i.node.direction === n.node.direction) && (i.parentId === e.id || n.parentId === e.id)) return [{ type: "resync" }];
	}
	if (n?.sideLayout) {
		let n = (e) => (e.children ?? []).some((e) => e.direction !== 0 && e.direction !== 1);
		if (n(e) || n(t)) return [{ type: "resync" }];
	}
	let a = /* @__PURE__ */ new Set();
	for (let e of r.keys()) i.has(e) || a.add(e);
	let o = /* @__PURE__ */ new Set();
	for (let e of i.keys()) r.has(e) || o.add(e);
	let s = [], c = /* @__PURE__ */ new Map(), l = /* @__PURE__ */ new Map(), u = (e, t, n) => {
		let r = c.get(t);
		r || c.set(t, r = []);
		let i = n === null ? r.length : r.indexOf(n);
		r.splice(i < 0 ? r.length : i, 0, e), l.set(e, t);
	}, d = (e) => {
		let t = l.get(e);
		if (t == null) return;
		let n = c.get(t);
		if (!n) return;
		let r = n.indexOf(e);
		r > -1 && n.splice(r, 1);
	}, f = (e) => {
		for (let t of e.children ?? []) u(t.id, e.id, null), f(t);
	};
	f(e), l.set(e.id, null);
	let p = Zt(t);
	for (let e of p) {
		if (!o.has(e)) continue;
		let t = i.get(e), n = t.parentId;
		if (n === null || o.has(n)) continue;
		let r = (e) => {
			let t = {}, n = Yt(e);
			for (let e in n) e !== "children" && e !== "parent" && (t[e] = n[e]);
			return e.children && (t.children = e.children.filter((e) => o.has(e.id)).map(r)), t;
		}, a = g(r(t.node)), l = c.get(n) ?? [], d = new Set(l), p = i.get(n).node.children ?? [], m = null;
		for (let e = t.index + 1; e < p.length; e++) if (d.has(p[e].id)) {
			m = p[e].id;
			break;
		}
		s.push({
			type: "insert",
			parentId: n,
			index: m === null ? l.length : l.indexOf(m),
			node: a
		}), u(e, n, m), f(a);
	}
	let m = [], h = /* @__PURE__ */ new Set();
	for (let e of p) {
		let t = i.get(e);
		t.parentId === null || h.has(t.parentId) || (h.add(t.parentId), m.push(t.parentId));
	}
	for (let e of m) {
		let t = (i.get(e).node.children ?? []).filter((e) => !a.has(e.id)).map((e) => e.id), n = new Set(t), r = (c.get(e) ?? []).filter((e) => n.has(e));
		if (r.length === t.length && r.every((e, n) => e === t[n])) continue;
		let o = null;
		for (let r = t.length - 1; r >= 0; r--) {
			let i = t[r], a = l.get(i) === e;
			if (a) {
				let t = c.get(e) ?? [], r = null;
				for (let e = t.indexOf(i) + 1; e < t.length; e++) if (n.has(t[e])) {
					r = t[e];
					break;
				}
				a = r === o;
			}
			a || (s.push({
				type: "move",
				id: i,
				parentId: e,
				before: o
			}), d(i), u(i, e, o)), o = i;
		}
	}
	for (let t of Zt(e)) {
		if (!a.has(t)) continue;
		let e = r.get(t).parentId;
		e !== null && a.has(e) || s.push({
			type: "remove",
			id: t
		});
	}
	for (let e of p) {
		let t = r.get(e);
		if (!t) continue;
		let n = i.get(e), a = "children" in n.node;
		a !== "children" in t.node && s.push({
			type: "children",
			id: e,
			present: a
		});
		let o = null;
		for (let e of qt) Qt(Yt(t.node)[e], Yt(n.node)[e]) || (o ||= {}, o[e] = Yt(n.node)[e]);
		o && s.push({
			type: "update",
			id: e,
			patch: $t(o)
		});
	}
	return s;
}
var tn = (e) => {
	let t = e.parentElement?.parentElement?.lastElementChild;
	t?.tagName === "svg" && t.remove();
}, H = (e) => {
	let t = e.parent;
	for (; t;) {
		if (t.expanded === !1) return !1;
		t = t.parent;
	}
	return !0;
}, nn = (e, t) => {
	e.parent = t;
	for (let t of e.children ?? []) nn(t, e);
}, rn = function(e, t) {
	return e.direction === 2 ? e.container.querySelector(t.direction === 0 ? ".lhs" : ".rhs") : e.direction === 3 ? e.container.querySelector(".me-main.down") : e.container.querySelector(e.direction === 0 ? ".me-main.lhs" : ".me-main.rhs");
}, an = function(e, t, n) {
	let r = t.parentElement;
	if (!r) return null;
	if (!r.children[1]) {
		let t = e.createChildren([]);
		return r.appendChild(_e(n.expanded)), r.insertAdjacentElement("afterend", t), t;
	}
	let i = r.nextElementSibling;
	return i?.classList.contains("me-children") ? i : null;
}, on = (e, t, n, r) => {
	let i = n.children ?? [];
	for (let n = i.indexOf(t) + 1; n < i.length; n++) {
		let t = r.get(i[n].id)?.parentElement?.parentElement;
		if (t?.parentElement === e) return t;
	}
	return null;
}, sn = (e, t, n) => {
	(t.parentElement !== e || t.nextElementSibling !== n) && e.insertBefore(t, n);
}, cn = function(e, t, n, r, i) {
	let a = t.parentNode, o = a.children[1];
	o && (o.expanded = r, o.className = "me-epd" + (r ? " minus" : "")), tn(t);
	let s = a.parentNode;
	if (r) {
		let t = e.createChildren((n.children ?? []).map((t) => e.createWrapper(t).grp));
		s.appendChild(t);
		for (let e of t.querySelectorAll(".me-tpc")) i.set(e.nodeObj.id, e);
	} else {
		let e = s.children[1];
		if (e && e.classList.contains("me-children")) {
			for (let t of e.querySelectorAll(".me-tpc")) i.delete(t.nodeObj.id);
			e.remove();
		}
	}
}, ln = (e, t) => {
	let n = (e.parentElement?.parentNode)?.children[1];
	if (n?.classList.contains("me-children")) {
		for (let e of n.querySelectorAll(".me-tpc")) t.delete(e.nodeObj.id);
		(n.previousElementSibling?.children[1])?.remove(), n.remove();
	}
}, un = function(e, t, n = !1) {
	for (let e of t) if (e.type === "resync") return !1;
	let r = e.nodeData;
	if (!r) return !1;
	let i = /* @__PURE__ */ new Map(), a = /* @__PURE__ */ new Map(), o = (e, t) => {
		e.parent = t, i.set(e.id, e);
		for (let t of e.children ?? []) o(t, e);
	}, s = (e) => {
		i.delete(e.id);
		for (let t of e.children ?? []) s(t);
	}, c = (e) => {
		for (let t of e.querySelectorAll(".me-tpc")) a.set(t.nodeObj.id, t);
	};
	o(r, void 0), c(e.map);
	for (let n of t) if (n.type === "insert") {
		let t = i.get(n.parentId);
		if (!t) continue;
		let s = g(n.node);
		t.children ||= [], t.children.splice(Math.min(Math.max(n.index, 0), t.children.length), 0, s), o(s, t);
		let l = a.get(n.parentId), u = null;
		if (t.id === r.id ? u = rn(e, s) : l && t.expanded !== !1 && H(t) && (u = an(e, l, t)), !u) continue;
		let { grp: d } = e.createWrapper(s);
		sn(u, d, on(u, s, t, a)), c(d);
	} else if (n.type === "move") {
		let t = i.get(n.id), o = i.get(n.parentId);
		if (!t || !o) continue;
		let s = t.parent, c = s ? a.get(s.id) : void 0, l = s ? H(s) : !1;
		if (s?.children) {
			let e = s.children.indexOf(t);
			e > -1 && s.children.splice(e, 1);
		}
		o.children ||= [];
		let u = n.before === null ? void 0 : o.children.find((e) => e.id === n.before), d = u ? o.children.indexOf(u) : -1;
		d < 0 ? o.children.push(t) : o.children.splice(d, 0, t), t.parent = o;
		let f = !!s && !!c && l && (s.children?.length ?? 0) === 0, p = a.get(n.id), m = p?.parentElement?.parentElement, h = a.get(n.parentId);
		if (!p || !m) {
			f && ln(c, a);
			continue;
		}
		if (o.id !== r.id && (!h || o.expanded === !1 || !H(o))) {
			f && ln(c, a);
			continue;
		}
		let g = o.id === r.id ? rn(e, t) : an(e, h, o);
		g && sn(g, m, on(g, t, o, a)), f && ln(c, a);
	} else if (n.type === "remove") {
		let e = i.get(n.id);
		if (!e) continue;
		let t = e.parent, r = a.get(n.id), o = t?.children ? t.children.length - 1 : 0;
		if (r && H(e)) {
			tn(r), Te(r, o);
			for (let e of r.querySelectorAll(".me-tpc")) a.delete(e.nodeObj.id);
		}
		if (a.delete(n.id), t?.children) {
			let n = t.children.indexOf(e);
			n > -1 && t.children.splice(n, 1);
		}
		s(e);
	} else if (n.type === "children") {
		let e = i.get(n.id);
		if (!e) continue;
		n.present ? e.children ||= [] : e.children && e.children.length === 0 && delete e.children;
	} else if (n.type === "update") {
		let t = i.get(n.id);
		if (!t) continue;
		let r = n.patch, o = !1;
		for (let e in r) e !== "children" && e !== "parent" && e !== "expanded" && (t[e] = r[e] === void 0 ? void 0 : g(r[e]), Jt.has(e) && (o = !0));
		let s = a.get(n.id);
		if (s && o && ("style" in r && s.removeAttribute("style"), ce.call(e, s, t)), !("expanded" in r)) continue;
		let c = t.expanded === !1 != (r.expanded === !1);
		if (t.expanded = r.expanded, !c || !s || !t.children?.length || !H(t)) continue;
		cn(e, s, t, t.expanded !== !1, a);
	}
	return nn(r, void 0), (t.length || n) && e.linkDiv(), !0;
};
//#endregion
//#region src/plugin/diffRefresh.ts
function dn(e) {
	e.diffRefresh = function(e) {
		if (!e?.nodeData || !this.nodeData || this.isFocusMode) return this.refresh(e), !1;
		let t = JSON.parse(JSON.stringify(e)), n = en(this.nodeData, t.nodeData, { sideLayout: this.direction === 2 });
		if (n.some((e) => e.type === "resync")) return this.refresh(e), !1;
		this.clearSelection(), this.isFocusMode = !1, this.nodeDataBackup = this.nodeData, this.bus.fire("refresh");
		let r = !Qt(this.arrows, t.arrows) || !Qt(this.summaries, t.summaries);
		return r && (this.arrows = t.arrows || [], this.summaries = t.summaries || []), t.meta && (this.meta = t.meta), un(this, n, r), !0;
	};
}
//#endregion
//#region src/utils/historyStack.ts
var fn = class {
	entries = [];
	index = 0;
	restorers = /* @__PURE__ */ new Map();
	listeners = [];
	register(e, t) {
		return this.restorers.set(e, t), () => {
			this.restorers.get(e) === t && this.restorers.delete(e);
		};
	}
	subscribe(e) {
		return this.listeners.push(e), () => {
			let t = this.listeners.indexOf(e);
			t !== -1 && this.listeners.splice(t, 1);
		};
	}
	push(e, t, n, r) {
		this.entries.length = this.index, this.entries.push({
			doc: e,
			before: t,
			after: n,
			meta: r,
			time: Date.now()
		}), this.index = this.entries.length, this.emit();
	}
	get canUndo() {
		return this.index > 0;
	}
	get canRedo() {
		return this.index < this.entries.length;
	}
	get size() {
		return this.entries.length;
	}
	get currentIndex() {
		return this.index;
	}
	getEntries() {
		return this.entries;
	}
	undo() {
		if (!this.canUndo) return null;
		this.index--;
		let e = this.entries[this.index];
		return this.restorers.get(e.doc)?.(e, "undo"), this.emit(), e;
	}
	redo() {
		if (!this.canRedo) return null;
		let e = this.entries[this.index];
		return this.index++, this.restorers.get(e.doc)?.(e, "redo"), this.emit(), e;
	}
	clear() {
		this.entries.length = 0, this.index = 0, this.emit();
	}
	emit() {
		this.listeners.forEach((e) => e());
	}
}, pn = function(e) {
	switch (e.name) {
		case "createSummary":
		case "finishEditSummary":
		case "removeSummary": return {
			type: "summary",
			value: e.target.id
		};
		case "createArrow":
		case "finishEditArrowLabel":
		case "removeArrow":
		case "reshapeArrow": return {
			type: "arrow",
			value: e.target.id
		};
		case "removeNodes":
		case "copyNodes":
		case "moveNodesBefore":
		case "moveNodesAfter":
		case "moveNodesIn": return {
			type: "nodes",
			value: e.target.map((e) => e.id)
		};
		case "expandNode":
		case "collapseNode": return {
			type: "nodes",
			value: [e.target.id]
		};
		default: return {
			type: "nodes",
			value: [e.target.id]
		};
	}
};
function mn(e) {
	let t = new fn(), n = [], r = e.getData(), i = !1, a = function() {
		i || (r = e.getData());
	}, o = (t) => {
		let n = [];
		t.forEach((t) => {
			try {
				n.push(e.findEle(t));
			} catch {}
		}), n.length && (e.selectNodes(n), e.scrollIntoView(n[n.length - 1]));
	}, s = (e, t) => {
		if (e.id === t) return e;
		for (let n of e.children ?? []) {
			let e = s(n, t);
			if (e) return e;
		}
		return null;
	};
	t.register("map", (t, n) => {
		let a = t.meta, c = n === "undo" ? t.before : t.after, l = e.isFocusMode ? e.nodeData?.id : null;
		if (i = !0, e.diffRefresh ? e.diffRefresh(c) : e.refresh(c), i = !1, l) {
			let t = e.nodeData, n = s(t, l);
			n ? (e.nodeDataBackup = t, e.nodeData = n, e.isFocusMode = !0, e.refresh()) : (e.nodeDataBackup = t, e.isFocusMode = !1, e.tempDirection = null);
		}
		if (r = c, !a) return;
		let { currentTarget: u, operation: d, currentSelected: f } = a, p = d === "removeNodes" || d === "removeSummary" || d === "removeArrow", m = d === "expandNode" || d === "collapseNode", h = u.type !== "nodes", g = !m && (h || n === "undo" === p);
		if (u.type === "nodes") {
			o(g ? u.value : f);
			return;
		}
		let _ = u.type === "summary" ? "s-" : "a-";
		if (g) {
			let t = e.nodes.querySelector(`#${CSS.escape(_ + u.value)}`);
			if (t) {
				u.type === "summary" ? e.selectSummary(t) : e.selectArrow(t);
				return;
			}
		}
		o(f);
	}), e.historyStack = t, e.undo = function() {
		t.undo();
	}, e.redo = function() {
		t.redo();
	}, e.clearHistory = function() {
		t.clear(), e.clearSelection(), r = e.getData();
	};
	let c = function(i) {
		if (i.name === "beginEdit" || i.silent) return;
		let a = e.getData();
		t.push("map", r, a, {
			operation: i.name,
			currentSelected: n,
			currentTarget: pn(i)
		}), r = a;
	}, l = function(t) {
		if (!e.editable || !t.metaKey && !t.ctrlKey) return;
		let n = t.key.toLowerCase();
		n === "z" ? t.shiftKey ? e.redo() : e.undo() : n === "y" && e.redo();
	}, u = function() {
		n = e.currentNodes.map((e) => e.nodeObj.id);
	};
	return e.bus.addListener("operation", c), e.bus.addListener("refresh", a), e.bus.addListener("selectNodes", u), e.bus.addListener("unselectNodes", u), e.container.addEventListener("keydown", l), () => {
		t.clear(), e.bus.removeListener("operation", c), e.bus.removeListener("refresh", a), e.bus.removeListener("selectNodes", u), e.bus.removeListener("unselectNodes", u), e.container.removeEventListener("keydown", l);
	};
}
//#endregion
//#region src/plugin/toolBar.ts
var hn = {
	side: "<?xml version=\"1.0\" standalone=\"no\"?><!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\"><svg t=\"1750169394918\" class=\"icon\" viewBox=\"0 0 1024 1024\" version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" p-id=\"2021\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" width=\"200\" height=\"200\"><path d=\"M851.91168 328.45312c-59.97056 0-108.6208 48.47104-108.91264 108.36992l-137.92768 38.4a109.14304 109.14304 0 0 0-63.46752-46.58688l1.39264-137.11872c47.29344-11.86816 82.31936-54.66624 82.31936-105.64096 0-60.15488-48.76288-108.91776-108.91776-108.91776s-108.91776 48.76288-108.91776 108.91776c0 49.18784 32.60928 90.75712 77.38368 104.27392l-1.41312 138.87488a109.19936 109.19936 0 0 0-63.50336 48.55808l-138.93632-39.48544 0.01024-0.72704c0-60.15488-48.76288-108.91776-108.91776-108.91776s-108.91776 48.75776-108.91776 108.91776c0 60.15488 48.76288 108.91264 108.91776 108.91264 39.3984 0 73.91232-20.92032 93.03552-52.2496l139.19232 39.552-0.00512 0.2304c0 25.8304 9.00096 49.5616 24.02816 68.23424l-90.14272 132.63872a108.7488 108.7488 0 0 0-34.2528-5.504c-60.15488 0-108.91776 48.768-108.91776 108.91776 0 60.16 48.76288 108.91776 108.91776 108.91776 60.16 0 108.92288-48.75776 108.92288-108.91776 0-27.14624-9.9328-51.968-26.36288-71.04l89.04704-131.03104a108.544 108.544 0 0 0 37.6832 6.70208 108.672 108.672 0 0 0 36.48512-6.272l93.13792 132.57216a108.48256 108.48256 0 0 0-24.69888 69.0688c0 60.16 48.768 108.92288 108.91776 108.92288 60.16 0 108.91776-48.76288 108.91776-108.92288 0-60.14976-48.75776-108.91776-108.91776-108.91776a108.80512 108.80512 0 0 0-36.69504 6.3488l-93.07136-132.48a108.48768 108.48768 0 0 0 24.79616-72.22784l136.09984-37.888c18.99008 31.93856 53.84192 53.3504 93.69088 53.3504 60.16 0 108.92288-48.75776 108.92288-108.91264-0.00512-60.15488-48.77312-108.92288-108.92288-108.92288z\" p-id=\"2022\"></path></svg>",
	left: "<?xml version=\"1.0\" standalone=\"no\"?><!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\"><svg t=\"1750169375313\" class=\"icon\" viewBox=\"0 0 1024 1024\" version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" p-id=\"1775\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" width=\"200\" height=\"200\"><path d=\"M639 463.30000001L639 285.1c0-36.90000001-26.4-68.5-61.3-68.5l-150.2 0c-1.5 0-3 0.1-4.5 0.3-10.2-38.7-45.5-67.3-87.5-67.3-50 0-90.5 40.5-90.5 90.5s40.5 90.5 90.5 90.5c42 0 77.3-28.6 87.5-67.39999999 1.4 0.3 2.9 0.4 4.5 0.39999999L577.7 263.6c6.8 0 14.3 8.9 14.3 21.49999999l0 427.00000001c0 12.7-7.40000001 21.5-14.30000001 21.5l-150.19999999 0c-1.5 0-3 0.2-4.5 0.4-10.2-38.8-45.5-67.3-87.5-67.3-50 0-90.5 40.5-90.5 90.4 0 49.9 40.5 90.6 90.5 90.59999999 42 0 77.3-28.6 87.5-67.39999999 1.4 0.2 2.9 0.4 4.49999999 0.4L577.7 780.7c34.80000001 0 61.3-31.6 61.3-68.50000001L639 510.3l79.1 0c10.4 38.5 45.49999999 67 87.4 67 50 0 90.5-40.5 90.5-90.5s-40.5-90.5-90.5-90.5c-41.79999999 0-77.00000001 28.4-87.4 67L639 463.30000001z\" fill=\"currentColor\" p-id=\"1776\"></path></svg>",
	right: "<?xml version=\"1.0\" standalone=\"no\"?><!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\"><svg t=\"1750169667709\" class=\"icon\" viewBox=\"0 0 1024 1024\" version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" p-id=\"3037\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" width=\"200\" height=\"200\"><path d=\"M385 560.69999999L385 738.9c0 36.90000001 26.4 68.5 61.3 68.5l150.2 0c1.5 0 3-0.1 4.5-0.3 10.2 38.7 45.5 67.3 87.5 67.3 50 0 90.5-40.5 90.5-90.5s-40.5-90.5-90.5-90.5c-42 0-77.3 28.6-87.5 67.39999999-1.4-0.3-2.9-0.4-4.5-0.39999999L446.3 760.4c-6.8 0-14.3-8.9-14.3-21.49999999l0-427.00000001c0-12.7 7.40000001-21.5 14.30000001-21.5l150.19999999 0c1.5 0 3-0.2 4.5-0.4 10.2 38.8 45.5 67.3 87.5 67.3 50 0 90.5-40.5 90.5-90.4 0-49.9-40.5-90.6-90.5-90.59999999-42 0-77.3 28.6-87.5 67.39999999-1.4-0.2-2.9-0.4-4.49999999-0.4L446.3 243.3c-34.80000001 0-61.3 31.6-61.3 68.50000001L385 513.7l-79.1 0c-10.4-38.5-45.49999999-67-87.4-67-50 0-90.5 40.5-90.5 90.5s40.5 90.5 90.5 90.5c41.79999999 0 77.00000001-28.4 87.4-67L385 560.69999999z\" fill=\"currentColor\" p-id=\"3038\"></path></svg>",
	full: "<?xml version=\"1.0\" standalone=\"no\"?><!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\"><svg t=\"1750169402629\" class=\"icon\" viewBox=\"0 0 1024 1024\" version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" p-id=\"2170\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" width=\"200\" height=\"200\"><path d=\"M639.328 416c8.032 0 16.096-3.008 22.304-9.056l202.624-197.184-0.8 143.808c-0.096 17.696 14.144 32.096 31.808 32.192 0.064 0 0.128 0 0.192 0 17.6 0 31.904-14.208 32-31.808l1.248-222.208c0-0.672-0.352-1.248-0.384-1.92 0.032-0.512 0.288-0.896 0.288-1.408 0.032-17.664-14.272-32-31.968-32.032L671.552 96l-0.032 0c-17.664 0-31.968 14.304-32 31.968C639.488 145.632 653.824 160 671.488 160l151.872 0.224-206.368 200.8c-12.672 12.32-12.928 32.608-0.64 45.248C622.656 412.736 630.976 416 639.328 416z\" p-id=\"2171\"></path><path d=\"M896.032 639.552 896.032 639.552c-17.696 0-32 14.304-32.032 31.968l-0.224 151.872-200.832-206.4c-12.32-12.64-32.576-12.96-45.248-0.64-12.672 12.352-12.928 32.608-0.64 45.248l197.184 202.624-143.808-0.8c-0.064 0-0.128 0-0.192 0-17.6 0-31.904 14.208-32 31.808-0.096 17.696 14.144 32.096 31.808 32.192l222.24 1.248c0.064 0 0.128 0 0.192 0 0.64 0 1.12-0.32 1.76-0.352 0.512 0.032 0.896 0.288 1.408 0.288l0.032 0c17.664 0 31.968-14.304 32-31.968L928 671.584C928.032 653.952 913.728 639.584 896.032 639.552z\" p-id=\"2172\"></path><path d=\"M209.76 159.744l143.808 0.8c0.064 0 0.128 0 0.192 0 17.6 0 31.904-14.208 32-31.808 0.096-17.696-14.144-32.096-31.808-32.192L131.68 95.328c-0.064 0-0.128 0-0.192 0-0.672 0-1.248 0.352-1.888 0.384-0.448 0-0.8-0.256-1.248-0.256 0 0-0.032 0-0.032 0-17.664 0-31.968 14.304-32 31.968L96 352.448c-0.032 17.664 14.272 32 31.968 32.032 0 0 0.032 0 0.032 0 17.664 0 31.968-14.304 32-31.968l0.224-151.936 200.832 206.4c6.272 6.464 14.624 9.696 22.944 9.696 8.032 0 16.096-3.008 22.304-9.056 12.672-12.32 12.96-32.608 0.64-45.248L209.76 159.744z\" p-id=\"2173\"></path><path d=\"M362.368 617.056l-202.624 197.184 0.8-143.808c0.096-17.696-14.144-32.096-31.808-32.192-0.064 0-0.128 0-0.192 0-17.6 0-31.904 14.208-32 31.808l-1.248 222.24c0 0.704 0.352 1.312 0.384 2.016 0 0.448-0.256 0.832-0.256 1.312-0.032 17.664 14.272 32 31.968 32.032L352.448 928c0 0 0.032 0 0.032 0 17.664 0 31.968-14.304 32-31.968s-14.272-32-31.968-32.032l-151.936-0.224 206.4-200.832c12.672-12.352 12.96-32.608 0.64-45.248S375.008 604.704 362.368 617.056z\" p-id=\"2174\"></path></svg>",
	living: "<?xml version=\"1.0\" standalone=\"no\"?><!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\"><svg t=\"1750169573443\" class=\"icon\" viewBox=\"0 0 1024 1024\" version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" p-id=\"2883\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" width=\"200\" height=\"200\"><path d=\"M514.133333 488.533333m-106.666666 0a106.666667 106.666667 0 1 0 213.333333 0 106.666667 106.666667 0 1 0-213.333333 0Z\" fill=\"currentColor\" p-id=\"2884\"></path><path d=\"M512 64C264.533333 64 64 264.533333 64 512c0 236.8 183.466667 428.8 416 445.866667v-134.4c-53.333333-59.733333-200.533333-230.4-200.533333-334.933334 0-130.133333 104.533333-234.666667 234.666666-234.666666s234.666667 104.533333 234.666667 234.666666c0 61.866667-49.066667 153.6-145.066667 270.933334l-59.733333 68.266666V960C776.533333 942.933333 960 748.8 960 512c0-247.466667-200.533333-448-448-448z\" fill=\"currentColor\" p-id=\"2885\"></path></svg>",
	zoomin: "<?xml version=\"1.0\" standalone=\"no\"?><!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\"><svg t=\"1750169419447\" class=\"icon\" viewBox=\"0 0 1024 1024\" version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" p-id=\"2480\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" width=\"200\" height=\"200\"><path d=\"M863.328 482.56l-317.344-1.12L545.984 162.816c0-17.664-14.336-32-32-32s-32 14.336-32 32l0 318.4L159.616 480.064c-0.032 0-0.064 0-0.096 0-17.632 0-31.936 14.24-32 31.904C127.424 529.632 141.728 544 159.392 544.064l322.592 1.152 0 319.168c0 17.696 14.336 32 32 32s32-14.304 32-32l0-318.944 317.088 1.12c0.064 0 0.096 0 0.128 0 17.632 0 31.936-14.24 32-31.904C895.264 496.992 880.96 482.624 863.328 482.56z\" p-id=\"2481\"></path></svg>",
	zoomout: "<?xml version=\"1.0\" standalone=\"no\"?><!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\"><svg t=\"1750169426515\" class=\"icon\" viewBox=\"0 0 1024 1024\" version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" p-id=\"2730\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" width=\"200\" height=\"200\"><path d=\"M863.744 544 163.424 544c-17.664 0-32-14.336-32-32s14.336-32 32-32l700.32 0c17.696 0 32 14.336 32 32S881.44 544 863.744 544z\" p-id=\"2731\"></path></svg>"
}, U = (e, t) => {
	let n = document.createElement("span");
	return n.id = e, n.innerHTML = hn[t], n;
};
function gn(e) {
	let t = document.createElement("div"), n = U("fullscreen", "full"), r = U("toCenter", "living"), i = U("zoomout", "zoomout"), a = U("zoomin", "zoomin");
	t.appendChild(n), t.appendChild(r), t.appendChild(i), t.appendChild(a), t.className = "mind-elixir-toolbar rb";
	let o = null, s = () => {
		let t = e.container.getBoundingClientRect(), n = x(e.map.style.transform), r = t.width / 2, i = t.height / 2;
		o = {
			containerRect: t,
			currentTransform: n,
			mapCenterX: (r - n.x) / e.scaleVal,
			mapCenterY: (i - n.y) / e.scaleVal
		};
	}, c = () => {
		if (o) {
			let t = e.container.getBoundingClientRect(), n = t.width / 2, r = t.height / 2, i = n - o.mapCenterX * e.scaleVal, a = r - o.mapCenterY * e.scaleVal, s = i - o.currentTransform.x, c = a - o.currentTransform.y;
			e.move(s, c);
		}
	}, l = e.el;
	l.addEventListener("fullscreenchange", c);
	let u = !1;
	return n.onclick = () => {
		s(), document.fullscreenElement === e.el ? document.exitFullscreen() : e.el.requestFullscreen();
	}, r.onclick = () => {
		e.toCenter();
	}, i.onclick = () => {
		e.scale(e.scaleVal - e.scaleSensitivity);
	}, a.onclick = () => {
		e.scale(e.scaleVal + e.scaleSensitivity);
	}, {
		element: t,
		dispose: () => {
			u || (u = !0, l.removeEventListener("fullscreenchange", c), o = null);
		}
	};
}
function _n(e) {
	let t = document.createElement("div"), n = U("tbltl", "left"), r = U("tbltr", "right"), i = U("tblts", "side");
	return t.appendChild(n), t.appendChild(r), t.appendChild(i), t.className = "mind-elixir-toolbar lt", n.onclick = () => {
		e.initLeft();
	}, r.onclick = () => {
		e.initRight();
	}, i.onclick = () => {
		e.initSide();
	}, t;
}
function vn(e) {
	let t = gn(e);
	return e.container.append(t.element), e.container.append(_n(e)), t.dispose;
}
//#endregion
//#region src/viselect/src/EventEmitter.ts
var yn = class {
	_listeners = /* @__PURE__ */ new Map();
	addEventListener(e, t) {
		let n = this._listeners.get(e) ?? /* @__PURE__ */ new Set();
		return this._listeners.set(e, n), n.add(t), this;
	}
	removeEventListener(e, t) {
		return this._listeners.get(e)?.delete(t), this;
	}
	dispatchEvent(e, ...t) {
		let n = !0;
		for (let r of this._listeners.get(e) ?? []) n = r(...t) !== !1 && n;
		return n;
	}
	unbindAllListeners() {
		this._listeners.clear();
	}
	on = this.addEventListener;
	off = this.removeEventListener;
	emit = this.dispatchEvent;
}, bn = (e, t = "px") => typeof e == "number" ? e + t : e, W = ({ style: e }, t, n) => {
	if (typeof t == "object") for (let [n, r] of Object.entries(t)) r !== void 0 && (e[n] = bn(r));
	else n !== void 0 && (e[t] = bn(n));
}, xn = (e = 0, t = 0, n = 0, r = 0) => {
	let i = {
		x: e,
		y: t,
		width: n,
		height: r,
		top: t,
		left: e,
		right: e + n,
		bottom: t + r
	}, a = () => JSON.stringify(i);
	return {
		...i,
		toJSON: a
	};
}, Sn = (e) => {
	let t, n = -1, r = !1;
	return {
		next: (...i) => {
			t = i, r || (r = !0, n = requestAnimationFrame(() => {
				e(...t), r = !1;
			}));
		},
		cancel: () => {
			cancelAnimationFrame(n), r = !1;
		}
	};
}, Cn = (e, t, n = "touch") => {
	switch (n) {
		case "center": {
			let n = t.left + t.width / 2, r = t.top + t.height / 2;
			return n >= e.left && n <= e.right && r >= e.top && r <= e.bottom;
		}
		case "cover": return t.left >= e.left && t.top >= e.top && t.right <= e.right && t.bottom <= e.bottom;
		case "touch": return e.right >= t.left && e.left <= t.right && e.bottom >= t.top && e.top <= t.bottom;
	}
}, wn = () => matchMedia("(hover: none), (pointer: coarse)").matches, Tn = () => "safari" in window, En = (e) => Array.isArray(e) ? e : [e], Dn = (e) => (t, n, r, i = {}) => {
	(t instanceof HTMLCollection || t instanceof NodeList) && (t = Array.from(t)), n = En(n), t = En(t);
	for (let a of t) if (a) for (let t of n) a[e](t, r, {
		capture: !1,
		...i
	});
}, On = Dn("addEventListener"), G = Dn("removeEventListener"), K = (e) => {
	let { clientX: t, clientY: n, target: r } = e.touches?.[0] ?? e;
	return {
		x: t,
		y: n,
		target: r
	};
}, q = (e, t = document) => En(e).map((e) => typeof e == "string" ? Array.from(t.querySelectorAll(e)) : e instanceof Element ? e : null).flat().filter(Boolean), kn = (e, t) => t.some((t) => typeof t == "number" ? e.button === t : typeof t == "object" && t.button === e.button && t.modifiers.every((t) => {
	switch (t) {
		case "alt": return e.altKey;
		case "ctrl": return e.ctrlKey || e.metaKey;
		case "shift": return e.shiftKey;
	}
})), { abs: J, max: An, min: jn, ceil: Mn } = Math, Nn = (e = []) => ({
	stored: e,
	selected: [],
	touched: [],
	changed: {
		added: [],
		removed: []
	}
}), Pn = class extends yn {
	static version = "mind-elixir-fork";
	_options;
	_selection = Nn();
	_area;
	_clippingElement;
	_targetElement;
	_targetBoundary;
	_targetBoundaryScrolled = !0;
	_targetRect;
	_selectables = [];
	_latestElement;
	_pointerTarget;
	_pointerId = null;
	_areaLocation = {
		y1: 0,
		x2: 0,
		y2: 0,
		x1: 0
	};
	_areaRect = xn();
	_singleClick = !0;
	_frame;
	_scrollAvailable = !0;
	_scrollingActive = !1;
	_scrollSpeed = {
		x: 0,
		y: 0
	};
	_scrollDelta = {
		x: 0,
		y: 0
	};
	constructor(e) {
		super(), this._options = {
			selectionAreaClass: "selection-area",
			selectionContainerClass: void 0,
			selectables: [],
			document: window.document,
			startAreas: ["html"],
			boundaries: ["html"],
			container: "body",
			manual: !0,
			mindElixirInstance: void 0,
			...e,
			behaviour: {
				overlap: "invert",
				intersect: "touch",
				triggers: [0],
				...e.behaviour,
				startThreshold: e.behaviour?.startThreshold ? typeof e.behaviour.startThreshold == "number" ? e.behaviour.startThreshold : {
					x: 10,
					y: 10,
					...e.behaviour.startThreshold
				} : {
					x: 10,
					y: 10
				},
				scrolling: {
					speedDivider: 10,
					...e.behaviour?.scrolling,
					startScrollMargins: {
						x: 0,
						y: 0,
						...e.behaviour?.scrolling?.startScrollMargins
					}
				}
			},
			features: {
				range: !0,
				touch: !0,
				deselectOnBlur: !1,
				...e.features,
				singleTap: {
					allow: !0,
					intersect: "native",
					...e.features?.singleTap
				}
			}
		};
		for (let e of Object.getOwnPropertyNames(Object.getPrototypeOf(this))) typeof this[e] == "function" && (this[e] = this[e].bind(this));
		let { document: t, selectionAreaClass: n, selectionContainerClass: r } = this._options;
		this._area = t.createElement("div"), this._clippingElement = t.createElement("div"), this._clippingElement.appendChild(this._area), this._area.classList.add(n), r && this._clippingElement.classList.add(r), W(this._area, {
			willChange: "top, left, bottom, right, width, height",
			top: 0,
			left: 0,
			position: "fixed"
		}), W(this._clippingElement, {
			overflow: "hidden",
			position: "fixed",
			transform: "translate3d(0, 0, 0)",
			pointerEvents: "none",
			zIndex: "1"
		}), this._frame = Sn((e) => {
			this._recalculateSelectionAreaRect(), this._updateElementSelection(), this._emitEvent("move", e), this._redrawSelectionArea();
		});
	}
	_onTapStart(e) {
		let { x: t, y: n, target: r } = K(e), { document: i, startAreas: a, boundaries: o, behaviour: s, features: c } = this._options, l = r.getBoundingClientRect();
		if (!kn(e, s.triggers)) return !1;
		let u = q(a, i), d = q(o, i);
		this._targetElement = d.find((e) => Cn(e.getBoundingClientRect(), l));
		let f = e.composedPath(), p = u.find((e) => f.includes(e));
		if (this._targetBoundary = d.find((e) => f.includes(e)), !this._targetElement || !p || !this._targetBoundary) return !1;
		this._areaLocation = {
			x1: t,
			y1: n,
			x2: 0,
			y2: 0
		};
		let m = i.scrollingElement ?? i.body;
		return this._scrollDelta = {
			x: m.scrollLeft,
			y: m.scrollTop
		}, this._singleClick = !0, this._pointerTarget = r, this._pointerId = e.pointerId, r.setPointerCapture(e.pointerId), this.clearSelection(!1, !0), On(i, "scroll", this._onScroll), c.deselectOnBlur && (this._targetBoundaryScrolled = !1, On(this._targetBoundary, "scroll", this._onStartAreaScroll)), !0;
	}
	_onSingleTap(e) {
		let { singleTap: { intersect: t }, range: n } = this._options.features, r = K(e), i;
		if (t === "native") i = r.target;
		else if (t === "touch") {
			this.resolveSelectables();
			let { x: e, y: t } = r;
			i = this._selectables.find((n) => {
				let { right: r, left: i, top: a, bottom: o } = n.getBoundingClientRect();
				return e < r && e > i && t < o && t > a;
			});
		}
		if (!i) return;
		for (this.resolveSelectables(); !this._selectables.includes(i);) if (i.parentElement) i = i.parentElement;
		else {
			this._targetBoundaryScrolled || this.clearSelection();
			return;
		}
		let { stored: a } = this._selection;
		if (this._emitEvent("start", e), e.shiftKey && n && this._latestElement) {
			let e = this._latestElement, [t, n] = e.compareDocumentPosition(i) & 4 ? [i, e] : [e, i], r = [
				...this._selectables.filter((e) => e.compareDocumentPosition(t) & 4 && e.compareDocumentPosition(n) & 2),
				t,
				n
			];
			this.select(r), this._latestElement = e;
		} else a.includes(i) && (a.length === 1 || e.ctrlKey || a.every((e) => this._selection.stored.includes(e))) ? this.deselect(i) : (this.select(i), this._latestElement = i);
	}
	_delayedTapMove(e) {
		let { container: t, document: n, behaviour: { startThreshold: r } } = this._options, { x1: i, y1: a } = this._areaLocation, { x: o, y: s } = K(e);
		if (typeof r == "number" && J(o + s - (i + a)) >= r || typeof r == "object" && J(o - i) >= r.x || J(s - a) >= r.y) {
			if (this._emitEvent("beforedrag", e) === !1) return;
			W(this._area, "display", "block"), q(t, n)[0].appendChild(this._clippingElement), this.resolveSelectables(), this._singleClick = !1, this._targetRect = this._targetElement.getBoundingClientRect(), this._scrollAvailable = this._targetElement.scrollHeight !== this._targetElement.clientHeight || this._targetElement.scrollWidth !== this._targetElement.clientWidth, this._scrollAvailable && (this._selectables = this._selectables.filter((e) => this._targetElement.contains(e))), this._setupSelectionArea(), this._emitEvent("start", e), this._onTapMove(e);
		}
		this._handleMoveEvent(e);
	}
	_setupSelectionArea() {
		let { _clippingElement: e, _targetElement: t, _area: n } = this, r = this._targetRect = t.getBoundingClientRect();
		this._scrollAvailable ? (W(e, {
			top: r.top,
			left: r.left,
			width: r.width,
			height: r.height
		}), W(n, {
			marginTop: -r.top,
			marginLeft: -r.left
		})) : (W(e, {
			top: 0,
			left: 0,
			width: "100%",
			height: "100%"
		}), W(n, {
			marginTop: 0,
			marginLeft: 0
		}));
	}
	_onTapMove(e) {
		let { _scrollSpeed: t, _areaLocation: n, _options: r, _frame: i } = this, { speedDivider: a } = r.behaviour.scrolling, { x: o, y: s } = K(e);
		if (n.x2 = o, n.y2 = s, this._scrollAvailable && !this._scrollingActive && (t.y || t.x)) {
			this._scrollingActive = !0;
			let r = () => {
				if (!t.x && !t.y) {
					this._scrollingActive = !1;
					return;
				}
				let o = this._options.mindElixirInstance;
				if (o && o.move) {
					let e = t.x ? Mn(t.x / a) : 0, r = t.y ? Mn(t.y / a) : 0;
					(e || r) && (o.move(-e, -r), n.x1 -= e, n.y1 -= r);
				}
				i.next(e), requestAnimationFrame(r);
			};
			requestAnimationFrame(r);
		} else i.next(e);
		this._handleMoveEvent(e);
	}
	_handleMoveEvent(e) {
		let { features: t } = this._options;
		(t.touch && wn() || this._scrollAvailable && Tn()) && e.preventDefault();
	}
	_onScroll() {
		let { _scrollDelta: e, _options: { document: t } } = this, { scrollTop: n, scrollLeft: r } = t.scrollingElement ?? t.body;
		this._areaLocation.x1 += e.x - r, this._areaLocation.y1 += e.y - n, e.x = r, e.y = n, this._setupSelectionArea(), this._frame.next(null);
	}
	_onStartAreaScroll() {
		this._targetBoundaryScrolled = !0, G(this._targetElement, "scroll", this._onStartAreaScroll);
	}
	_recalculateSelectionAreaRect() {
		let { _scrollSpeed: e, _areaLocation: t, _targetElement: n, _options: r } = this, i = this._targetRect, { x1: a, y1: o } = t, { x2: s, y2: c } = t, { behaviour: { scrolling: { startScrollMargins: l } } } = r;
		s < i.left + l.x ? (e.x = -J(i.left - s + l.x), s = s < i.left ? i.left : s) : s > i.right - l.x ? (e.x = J(i.left + i.width - s - l.x), s = s > i.right ? i.right : s) : e.x = 0, c < i.top + l.y ? (e.y = -J(i.top - c + l.y), c = c < i.top ? i.top : c) : c > i.bottom - l.y ? (e.y = J(i.top + i.height - c - l.y), c = c > i.bottom ? i.bottom : c) : e.y = 0;
		let u = jn(a, s), d = jn(o, c), f = An(a, s), p = An(o, c);
		this._areaRect = xn(u, d, f - u, p - d);
	}
	_redrawSelectionArea() {
		let { x: e, y: t, width: n, height: r } = this._areaRect, { style: i } = this._area;
		i.left = `${e}px`, i.top = `${t}px`, i.width = `${n}px`, i.height = `${r}px`;
	}
	_onTapStop(e, t) {
		let { document: n, features: r } = this._options, { _singleClick: i } = this;
		this._pointerTarget && this._pointerId !== null && this._pointerTarget.hasPointerCapture(this._pointerId) && this._pointerTarget.releasePointerCapture(this._pointerId), this._pointerTarget = void 0, this._pointerId = null, G(this._targetElement, "scroll", this._onStartAreaScroll), G(n, ["pointermove"], this._delayedTapMove), G(n, ["pointermove"], this._onTapMove), G(n, ["pointerup", "pointercancel"], this._onTapStop), G(n, "scroll", this._onScroll), this._keepSelection(), e && i && r.singleTap.allow ? this._onSingleTap(e) : !i && !t && (this._updateElementSelection(), this._emitEvent("stop", e)), this._scrollSpeed.x = 0, this._scrollSpeed.y = 0, this._clippingElement.remove(), this._frame?.cancel(), W(this._area, "display", "none");
	}
	_updateElementSelection() {
		let { _selectables: e, _options: t, _selection: n, _areaRect: r } = this, { stored: i, selected: a, touched: o } = n, { intersect: s, overlap: c } = t.behaviour, l = c === "invert", u = [], d = [], f = [];
		for (let t = 0; t < e.length; t++) {
			let n = e[t];
			if (Cn(r, n.getBoundingClientRect(), s)) {
				if (a.includes(n)) i.includes(n) && !o.includes(n) && o.push(n);
				else if (l && i.includes(n)) {
					f.push(n);
					continue;
				} else d.push(n);
				u.push(n);
			}
		}
		l && d.push(...i.filter((e) => !a.includes(e)));
		let p = c === "keep";
		for (let e = 0; e < a.length; e++) {
			let t = a[e];
			!u.includes(t) && !(p && i.includes(t)) && f.push(t);
		}
		n.selected = u, n.changed = {
			added: d,
			removed: f
		}, this._latestElement = void 0;
	}
	_emitEvent(e, t) {
		return this.emit(e, {
			event: t,
			store: this._selection,
			selection: this
		});
	}
	_keepSelection() {
		let { _options: e, _selection: t } = this, { selected: n, changed: r, touched: i, stored: a } = t, o = n.filter((e) => !a.includes(e));
		switch (e.behaviour.overlap) {
			case "drop":
				t.stored = [...o, ...a.filter((e) => !i.includes(e))];
				break;
			case "invert":
				t.stored = [...o, ...a.filter((e) => !r.removed.includes(e))];
				break;
			case "keep": t.stored = [...a, ...n.filter((e) => !a.includes(e))];
		}
	}
	start(e) {
		return this._onTapStart(e);
	}
	move(e) {
		this._singleClick ? this._delayedTapMove(e) : this._onTapMove(e);
	}
	stop(e, t = !1) {
		let n = !this._singleClick;
		return this._onTapStop(e, t), n;
	}
	trigger(e) {
		return this._onTapStart(e);
	}
	resolveSelectables() {
		this._selectables = q(this._options.selectables, this._options.document);
	}
	clearSelection(e = !0, t = !1) {
		let { selected: n, stored: r, changed: i } = this._selection;
		i.added = [], i.removed.push(...n, ...e ? r : []), t || (this._emitEvent("move", null), this._emitEvent("stop", null)), this._selection = Nn(e ? [] : r);
	}
	getSelection() {
		return this._selection.stored;
	}
	getSelectionArea() {
		return this._area;
	}
	getSelectables() {
		return this._selectables;
	}
	setAreaLocation(e) {
		Object.assign(this._areaLocation, e), this._redrawSelectionArea();
	}
	getAreaLocation() {
		return this._areaLocation;
	}
	cancel(e = !1) {
		this._onTapStop(null, !e);
	}
	destroy() {
		this.cancel(), this._clippingElement.remove(), super.unbindAllListeners();
	}
	select(e, t = !1) {
		let { changed: n, selected: r, stored: i } = this._selection, a = q(e, this._options.document).filter((e) => !r.includes(e) && !i.includes(e));
		return i.push(...a), r.push(...a), n.added.push(...a), n.removed = [], this._latestElement = void 0, t || (this._emitEvent("move", null), this._emitEvent("stop", null)), a;
	}
	deselect(e, t = !1) {
		let { selected: n, stored: r, changed: i } = this._selection, a = q(e, this._options.document).filter((e) => n.includes(e) || r.includes(e));
		this._selection.stored = r.filter((e) => !a.includes(e)), this._selection.selected = n.filter((e) => !a.includes(e)), this._selection.changed.added = [], this._selection.changed.removed.push(...a.filter((e) => !i.removed.includes(e))), this._latestElement = void 0, t || (this._emitEvent("move", null), this._emitEvent("stop", null));
	}
};
//#endregion
//#region src/plugin/selection.ts
function Fn(e) {
	let t = e.mouseSelectionButton === 2 ? [2] : [0], n = new Pn({
		selectables: [".map-container .me-tpc"],
		boundaries: [e.container],
		container: e.selectionContainer,
		manual: !0,
		mindElixirInstance: e,
		features: {
			touch: !1,
			singleTap: { allow: !1 }
		},
		behaviour: {
			triggers: t,
			scrolling: {
				speedDivider: 10,
				startScrollMargins: {
					x: 50,
					y: 50
				}
			}
		}
	}), r = n.getSelectionArea();
	r.style.background = "#4f90f22d", r.style.border = "1px solid #4f90f2", r.style.borderRadius = "3px", n.on("move", ({ store: { changed: { added: t, removed: n } } }) => {
		if (t.length > 0) {
			let n = t.filter((t) => !e.currentNodes?.includes(t));
			if (n.length > 0) {
				for (let e of n) e.classList.add("selected");
				e.currentNodes = [...e.currentNodes || [], ...n], e.bus.fire("selectNodes", n.map((e) => e.nodeObj));
			}
		}
		if (n.length > 0) {
			let t = n.filter((t) => e.currentNodes?.includes(t));
			if (t.length > 0) {
				for (let e of t) e.classList.remove("selected");
				e.currentNodes = (e.currentNodes || []).filter((e) => !t.includes(e)), e.bus.fire("unselectNodes", t.map((e) => e.nodeObj));
			}
		}
	}), e.selection = n;
}
//#endregion
//#region src/utils/generateBranch.ts
var In = function(e, t, n, r, i = 8) {
	if (e === n) return `M ${e} ${t} V ${r}`;
	let a = (t + r) / 2, o = n > e ? 1 : -1, s = Math.min(i, Math.abs(n - e) / 2, Math.abs(a - t), Math.abs(r - a));
	return `M ${e} ${t} V ${a - s} Q ${e} ${a} ${e + o * s} ${a} H ${n - o * s} Q ${n} ${a} ${n} ${a + s} V ${r}`;
};
function Ln({ pT: e, pL: t, pW: n, pH: r, cT: i, cL: a, cW: o, cH: s, direction: c, containerHeight: l, containerWidth: u }) {
	if (c === P.DOWN) {
		let s = t + n / 2, c = a + o / 2;
		return In(s, e + r, c, i);
	}
	let d = t + n / 2, f = e + r / 2, p;
	p = c === P.LHS ? a + o : a;
	let m = i + s / 2, h = (1 - Math.abs(m - f) / l) * .25 * (n / 2);
	return d = c === P.LHS ? d - n / 10 - h : d + n / 10 + h, `M ${d} ${f} Q ${d} ${m} ${p} ${m}`;
}
function Rn({ pT: e, pL: t, pW: n, pH: r, cT: i, cL: a, cW: o, cH: s, direction: c, isFirst: l }) {
	if (c === P.DOWN) return In(t + n / 2, e + r, a + o / 2, i);
	let u = parseInt(this.container.style.getPropertyValue("--node-gap-x")), d = 0, f = 0;
	d = l ? e + r / 2 : e + r;
	let p = i + s, m = 0, h = 0, g = 0, _ = Math.min(Math.abs(d - p) / 300 * u, u);
	return c === P.LHS ? (g = t, m = g + u, h = g - u, f = a + u, `M ${m} ${d} C ${g - _} ${d} ${g + _} ${p} ${h} ${p} H ${f}`) : (g = t + n, m = g - u, h = g + u, f = a + o - u, `M ${m} ${d} C ${g + _} ${d} ${g - _} ${p} ${h} ${p} H ${f}`);
}
//#endregion
//#region src/utils/theme.ts
var zn = function(e, t = !0) {
	this.theme = e, this.generateMainBranch = this.theme.generateMainBranch || Ln, this.generateSubBranch = this.theme.generateSubBranch || Rn;
	let n = {
		...(this.theme.type === "dark" ? s : o).cssVar,
		...this.theme.cssVar
	};
	this.compact && (n["--node-gap-x"] = "15px", n["--node-gap-y"] = "2px", n["--main-gap-x"] = "30px", n["--main-gap-y"] = "6px");
	let r = Object.keys(n);
	for (let e = 0; e < r.length; e++) {
		let t = r[e];
		this.container.style.setProperty(t, n[t]);
	}
	t && this.refresh();
}, Bn = function(e) {
	this.compact = e, this.theme && this.changeTheme(this.theme);
}, Vn = { create: function(e) {
	return {
		dom: e,
		moved: !1,
		sessionMoved: !1,
		pointerdown: !1,
		lastX: 0,
		lastY: 0,
		handlePointerMove(e) {
			if (this.pointerdown) {
				this.moved = !0, this.sessionMoved = !0;
				let t = e.clientX - this.lastX, n = e.clientY - this.lastY;
				this.lastX = e.clientX, this.lastY = e.clientY, this.cb && this.cb(t, n);
			}
		},
		handlePointerDown(e) {
			e.button === 0 && (this.pointerdown = !0, this.sessionMoved = !1, this.lastX = e.clientX, this.lastY = e.clientY, this.dom.setPointerCapture(e.pointerId));
		},
		handleClear(e) {
			let t = this.pointerdown && this.sessionMoved;
			this.pointerdown = !1, this.sessionMoved = !1, e.pointerId !== void 0 && this.dom.releasePointerCapture(e.pointerId), t && this.onEnd && this.onEnd();
		},
		cb: null,
		onEnd: null,
		init(e, t, n) {
			this.cb = t, this.onEnd = n || null, this.handleClear = this.handleClear.bind(this), this.handlePointerMove = this.handlePointerMove.bind(this), this.handlePointerDown = this.handlePointerDown.bind(this), this.destroy = S([
				{
					dom: e,
					evt: "pointermove",
					func: this.handlePointerMove
				},
				{
					dom: e,
					evt: "pointerleave",
					func: this.handleClear
				},
				{
					dom: e,
					evt: "pointerup",
					func: this.handleClear
				},
				{
					dom: this.dom,
					evt: "pointerdown",
					func: this.handlePointerDown
				}
			]);
		},
		destroy: null,
		clear() {
			this.moved = !1, this.pointerdown = !1;
		}
	};
} }, Hn = /* @__PURE__ */ t({
	createArrow: () => Yn,
	createArrowFrom: () => Xn,
	editArrowLabel: () => or,
	removeArrow: () => Zn,
	renderArrow: () => ar,
	reshapeArrow: () => cr,
	selectArrow: () => Qn,
	tidyArrow: () => sr,
	unselectArrow: () => $n
}), Un = "#4dc4ff";
function Wn(e, t, n, r, i, a, o, s) {
	return {
		x: e / 8 + n * 3 / 8 + i * 3 / 8 + o / 8,
		y: t / 8 + r * 3 / 8 + a * 3 / 8 + s / 8
	};
}
function Gn(e, t, n) {
	e && (e.dataset.x = t.toString(), e.dataset.y = n.toString(), B(e));
}
function Y(e, t, n, r, i) {
	v(e, {
		x1: t + "",
		y1: n + "",
		x2: r + "",
		y2: i + ""
	});
}
function Kn(e, t, n, r, i, a, o, s, c, l) {
	let u = `M ${t} ${n} C ${r} ${i} ${a} ${o} ${s} ${c}`;
	e.line.setAttribute("d", u);
	let d = l.style || {};
	e.line.setAttribute("stroke", d.stroke || "rgb(227, 125, 116)"), e.line.setAttribute("stroke-width", String(d.strokeWidth || "2")), e.line.setAttribute("stroke-dasharray", d.strokeDasharray || "8,2"), d.opacity !== void 0 && d.opacity !== null && d.opacity !== "" ? e.line.setAttribute("opacity", String(d.opacity)) : e.line.removeAttribute("opacity");
	let f = e.querySelectorAll("path[stroke=\"transparent\"]");
	f.length > 0 && f[0].setAttribute("d", u);
	let m = p(a, o, s, c);
	if (m) {
		let t = `M ${m.x1} ${m.y1} L ${s} ${c} L ${m.x2} ${m.y2}`;
		e.arrow1.setAttribute("d", t), f.length > 1 && f[1].setAttribute("d", t), e.arrow1.setAttribute("stroke", d.stroke || "rgb(227, 125, 116)"), e.arrow1.setAttribute("stroke-width", String(d.strokeWidth || "2")), d.opacity !== void 0 && d.opacity !== null && d.opacity !== "" ? e.arrow1.setAttribute("opacity", String(d.opacity)) : e.arrow1.removeAttribute("opacity");
	}
	if (l.bidirectional) {
		let a = p(r, i, t, n);
		if (a) {
			let r = `M ${a.x1} ${a.y1} L ${t} ${n} L ${a.x2} ${a.y2}`;
			e.arrow2.setAttribute("d", r), f.length > 2 && f[2].setAttribute("d", r);
		}
	} else e.arrow2.setAttribute("d", ""), f.length > 2 && f[2].setAttribute("d", "");
	e.arrow2.setAttribute("stroke", d.stroke || "rgb(227, 125, 116)"), e.arrow2.setAttribute("stroke-width", String(d.strokeWidth || "2")), d.opacity !== void 0 && d.opacity !== null && d.opacity !== "" ? e.arrow2.setAttribute("opacity", String(d.opacity)) : e.arrow2.removeAttribute("opacity");
	let { x: h, y: g } = Wn(t, n, r, i, a, o, s, c);
	e.labelEl && Gn(e.labelEl, h, g);
	let _ = e.labelEl;
	_ && (_.style.color = d.labelColor || "rgb(235, 95, 82)"), rr(e);
}
function X(e, t, n) {
	let { offsetLeft: r, offsetTop: i } = _(e.nodes, t), a = t.offsetWidth, o = t.offsetHeight, s = r + a / 2, c = i + o / 2;
	return {
		w: a,
		h: o,
		cx: s,
		cy: c,
		ctrlX: s + n.x,
		ctrlY: c + n.y
	};
}
function Z(e) {
	let t = e.w / 2, n = e.h / 2, r = e.ctrlX - e.cx, i = e.ctrlY - e.cy, a = Math.hypot(r, i);
	if (a === 0 || t === 0 && n === 0) return {
		x: e.cx,
		y: e.cy
	};
	let o = r / a, s = i / a, c = Math.min(t / Math.abs(o), n / Math.abs(s));
	return {
		x: e.cx + o * c,
		y: e.cy + s * c
	};
}
var qn = function(e, t, n) {
	let r = _(e.nodes, t), i = _(e.nodes, n), a = r.offsetLeft + t.offsetWidth / 2, o = r.offsetTop + t.offsetHeight / 2, s = i.offsetLeft + n.offsetWidth / 2, c = i.offsetTop + n.offsetHeight / 2, l = s - a, u = c - o, d = Math.sqrt(l * l + u * u), f = Math.max(50, Math.min(200, d * .3)), p = Math.abs(l), m = Math.abs(u), h, g;
	if (d < 150) {
		let e = t.closest(".me-main"), n = e ? e.classList.contains("lhs") ? -1 : 1 : l > 0 ? -1 : 1;
		h = {
			x: 200 * n,
			y: 0
		}, g = {
			x: 200 * n,
			y: 0
		};
	} else if (p > m * 1.5) {
		let e = l > 0 ? t.offsetWidth / 2 : -t.offsetWidth / 2, r = l > 0 ? -n.offsetWidth / 2 : n.offsetWidth / 2;
		h = {
			x: e + (l > 0 ? f : -f),
			y: 0
		}, g = {
			x: r + (l > 0 ? -f : f),
			y: 0
		};
	} else if (m > p * 1.5) {
		let e = u > 0 ? t.offsetHeight / 2 : -t.offsetHeight / 2, r = u > 0 ? -n.offsetHeight / 2 : n.offsetHeight / 2;
		h = {
			x: 0,
			y: e + (u > 0 ? f : -f)
		}, g = {
			x: 0,
			y: r + (u > 0 ? -f : f)
		};
	} else {
		let e = Math.atan2(u, l), r = t.offsetWidth / 2 * Math.cos(e), i = t.offsetHeight / 2 * Math.sin(e), a = -(n.offsetWidth / 2) * Math.cos(e), o = -(n.offsetHeight / 2) * Math.sin(e), s = f * .7 * (l > 0 ? 1 : -1), c = f * .7 * (u > 0 ? 1 : -1);
		h = {
			x: r + s,
			y: i + c
		}, g = {
			x: a - s,
			y: o - c
		};
	}
	return {
		delta1: {
			x: Math.round(h.x),
			y: Math.round(h.y)
		},
		delta2: {
			x: Math.round(g.x),
			y: Math.round(g.y)
		}
	};
}, Jn = function(e, t, n, r, i) {
	if (!t || !n) return;
	if (!r.delta1 || !r.delta2) {
		let i = qn(e, t, n);
		r.delta1 = i.delta1, r.delta2 = i.delta2;
	}
	let a = X(e, t, r.delta1), o = X(e, n, r.delta2), { x: s, y: c } = Z(a), { ctrlX: l, ctrlY: u } = a, { ctrlX: d, ctrlY: f } = o, { x: m, y: h } = Z(o), g = p(d, f, m, h);
	if (!g) return;
	let _ = `M ${g.x1} ${g.y1} L ${m} ${h} L ${g.x2} ${g.y2}`, v = "";
	if (r.bidirectional) {
		let e = p(l, u, s, c);
		if (!e) return;
		v = `M ${e.x1} ${e.y1} L ${s} ${c} L ${e.x2} ${e.y2}`;
	}
	let y = Bt(`M ${s} ${c} C ${l} ${u} ${d} ${f} ${m} ${h}`, _, v, r.style), { x: b, y: x } = Wn(s, c, l, u, d, f, m, h), S = r.style?.labelColor || "rgb(235, 95, 82)", C = "a-" + r.id;
	y.id = C;
	let w = Lt(e.markdown ? e.markdown(r.label, r) : r.label, b, x, {
		anchor: "middle",
		color: S,
		dataType: "arrow",
		svgId: C
	});
	y.labelEl = w, y.arrowObj = r, y.dataset.linkid = r.id, e.labelContainer.appendChild(w), e.arrowSvg.appendChild(y), B(w), i || (e.arrows.push(r), e.currentArrow = y, ir(e, r, a, o));
}, Yn = function(e, t, n = {}) {
	let r = {
		id: m(),
		label: "Custom Link",
		from: e.nodeObj.id,
		to: t.nodeObj.id,
		...n
	};
	Jn(this, e, t, r), this.bus.fire("operation", {
		name: "createArrow",
		target: r
	});
}, Xn = function(e) {
	Q(this);
	let t = {
		...e,
		id: m()
	};
	Jn(this, this.findEle(t.from), this.findEle(t.to), t), this.bus.fire("operation", {
		name: "createArrow",
		target: t
	});
}, Zn = function(e) {
	let t;
	if (t = e || this.currentArrow, !t) return;
	Q(this);
	let n = g(t.arrowObj);
	this.arrows = this.arrows.filter((e) => e.id !== n.id), t.labelEl?.remove(), t.remove(), this.bus.fire("operation", {
		name: "removeArrow",
		target: n
	});
}, Qn = function(e) {
	this.currentArrow = e;
	let t = e.arrowObj, n = this.findEle(t.from), r = this.findEle(t.to), i = X(this, n, t.delta1), a = X(this, r, t.delta2);
	this.editable ? ir(this, t, i, a) : tr(e, Un), this.bus.fire("selectArrow", t);
}, $n = function() {
	Q(this), this.currentArrow = null, this.bus.fire("unselectArrow");
}, er = function(e, t) {
	let n = document.createElementNS(z, "path");
	return v(n, {
		d: e,
		stroke: t,
		fill: "none",
		"stroke-width": "6",
		"stroke-linecap": "round",
		"stroke-linejoin": "round"
	}), n;
}, tr = function(e, t) {
	let n = document.createElementNS(z, "g");
	n.setAttribute("class", "arrow-highlight"), n.setAttribute("opacity", "0.45");
	let r = er(e.line.getAttribute("d"), t);
	n.appendChild(r);
	let i = er(e.arrow1.getAttribute("d"), t);
	if (n.appendChild(i), e.arrow2.getAttribute("d")) {
		let r = er(e.arrow2.getAttribute("d"), t);
		n.appendChild(r);
	}
	e.insertBefore(n, e.firstChild);
}, nr = function(e) {
	let t = e.querySelector(".arrow-highlight");
	t && t.remove();
}, rr = function(e) {
	let t = e.querySelector(".arrow-highlight");
	if (!t) return;
	let n = t.querySelectorAll("path");
	n.length >= 1 && n[0].setAttribute("d", e.line.getAttribute("d")), n.length >= 2 && n[1].setAttribute("d", e.arrow1.getAttribute("d")), n.length >= 3 && e.arrow2.getAttribute("d") && n[2].setAttribute("d", e.arrow2.getAttribute("d"));
}, Q = function(e) {
	e.helper1?.destroy(), e.helper2?.destroy(), e.linkController.style.display = "none", e.P2.style.display = "none", e.P3.style.display = "none", e.currentArrow && nr(e.currentArrow);
}, ir = function(e, t, n, r) {
	let { linkController: i, P2: a, P3: o, line1: s, line2: c, nodes: l, map: u, currentArrow: d, bus: f } = e;
	if (!d) return;
	i.style.display = "initial", a.style.display = "initial", o.style.display = "initial", l.appendChild(i), l.appendChild(a), l.appendChild(o), tr(d, Un);
	let { x: p, y: m } = Z(n), { ctrlX: h, ctrlY: _ } = n, { ctrlX: v, ctrlY: y } = r, { x: b, y: x } = Z(r);
	a.style.cssText = `top:${_}px;left:${h}px;`, o.style.cssText = `top:${y}px;left:${v}px;`, Y(s, p, m, h, _), Y(c, v, y, b, x), e.helper1 = Vn.create(a), e.helper2 = Vn.create(o);
	let S = g(t), C = () => {
		f.fire("operation", {
			name: "reshapeArrow",
			target: t,
			origin: S
		}), S = g(t);
	};
	e.helper1.init(u, (r, i) => {
		h += r / e.scaleVal, _ += i / e.scaleVal;
		let o = Z({
			...n,
			ctrlX: h,
			ctrlY: _
		});
		p = o.x, m = o.y, a.style.top = _ + "px", a.style.left = h + "px", Kn(d, p, m, h, _, v, y, b, x, t), Y(s, p, m, h, _), t.delta1.x = Math.round(h - n.cx), t.delta1.y = Math.round(_ - n.cy), f.fire("updateArrowDelta", t);
	}, C), e.helper2.init(u, (n, i) => {
		v += n / e.scaleVal, y += i / e.scaleVal;
		let a = Z({
			...r,
			ctrlX: v,
			ctrlY: y
		});
		b = a.x, x = a.y, o.style.top = y + "px", o.style.left = v + "px", Kn(d, p, m, h, _, v, y, b, x, t), Y(c, v, y, b, x), t.delta2.x = Math.round(v - r.cx), t.delta2.y = Math.round(y - r.cy), f.fire("updateArrowDelta", t);
	}, C);
};
function ar() {
	this.arrowSvg.innerHTML = "", this.labelContainer.querySelectorAll(".svg-label[data-type=\"arrow\"]").forEach((e) => e.remove());
	for (let e = 0; e < this.arrows.length; e++) {
		let t = this.arrows[e];
		try {
			Jn(this, this.findEle(t.from), this.findEle(t.to), t, !0);
		} catch {
			console.warn("Node may not be expanded");
		}
	}
	this.nodes.appendChild(this.arrowSvg);
}
function or(e) {
	Q(this), e && e.labelEl && Vt(this, e.labelEl, e.arrowObj);
}
function sr() {
	this.arrows = this.arrows.filter((e) => l(e.from, this.nodeData) && l(e.to, this.nodeData));
}
var cr = function(e, t) {
	let n = g(e);
	n.style && t.style && (t.style = Object.assign({}, n.style, t.style)), Object.assign(e, t);
	let r = this.arrowSvg.querySelector(`g[data-linkid="${e.id}"]`);
	if (r) {
		if (t.label !== void 0 && r.labelEl) {
			let t = this.markdown ? this.markdown(e.label, e) : e.label;
			r.labelEl.innerHTML = t;
		}
		let n = this.findEle(e.from), i = this.findEle(e.to);
		if (n && i) {
			if (!e.delta1 || !e.delta2) {
				let t = qn(this, n, i);
				e.delta1 = e.delta1 || t.delta1, e.delta2 = e.delta2 || t.delta2;
			}
			let t = X(this, n, e.delta1), a = X(this, i, e.delta2), { x: o, y: s } = Z(t), { ctrlX: c, ctrlY: l } = t, { ctrlX: u, ctrlY: d } = a, { x: f, y: p } = Z(a);
			Kn(r, o, s, c, l, u, d, f, p, e), this.currentArrow?.arrowObj?.id === e.id && (this.P2.style.cssText = `top:${l}px;left:${c}px;`, this.P3.style.cssText = `top:${d}px;left:${u}px;`, Y(this.line1, o, s, c, l), Y(this.line2, u, d, f, p));
		}
	}
	this.bus.fire("operation", {
		name: "reshapeArrow",
		target: e,
		origin: n
	});
}, lr = /* @__PURE__ */ t({
	createSummary: () => br,
	createSummaryFrom: () => xr,
	editSummary: () => Er,
	removeSummary: () => Sr,
	renderSummary: () => Tr,
	selectSummary: () => Cr,
	unselectSummary: () => wr
}), ur = function(e) {
	if (e.length === 0) return null;
	if (e.length === 1) {
		let t = e[0].nodeObj, n = e[0].nodeObj.parent;
		if (!n) return null;
		let r = n.children.findIndex((e) => t === e);
		return {
			parent: n.id,
			start: r,
			end: r
		};
	}
	let t = 0, n = e.map((e) => {
		let n = e.nodeObj, r = [];
		for (; n.parent;) {
			let e = n.parent, t = e.children?.indexOf(n);
			n = e, r.unshift({
				node: n,
				index: t
			});
		}
		return r.length > t && (t = r.length), r;
	}), r = 0;
	findMcp: for (; r < t; r++) {
		let e = n[0][r]?.node;
		for (let t = 1; t < n.length; t++) if (n[t][r]?.node !== e) break findMcp;
	}
	if (!r) return null;
	let i = n.map((e) => e[r - 1].index).sort((e, t) => e - t), a = i[0] || 0, o = i[i.length - 1] || 0, s = n[0][r - 1].node;
	return s.parent ? {
		parent: s.id,
		start: a,
		end: o
	} : null;
}, dr = function(e) {
	let t = document.createElementNS(z, "g");
	return t.setAttribute("id", e), t;
}, fr = function(e, t) {
	let n = document.createElementNS(z, "path");
	return v(n, {
		d: e,
		stroke: t || "#666",
		fill: "none",
		"stroke-linecap": "round",
		"stroke-width": "2"
	}), n;
}, pr = (e) => e.parentElement.parentElement, mr = 12, hr = 20, gr = function(e, t) {
	if (t.length === 0) return {
		order: [],
		contained: /* @__PURE__ */ new Map()
	};
	let n = /* @__PURE__ */ new Map();
	for (let e of t) {
		let t = n.get(e.parent);
		t ? t.push(e) : n.set(e.parent, [e]);
	}
	let r = /* @__PURE__ */ new Map(), i = /* @__PURE__ */ new Map(), a = [], o = (e) => {
		r.set(e.id, e);
		let t = e.children;
		if (t) for (let e = 0; e < t.length; e++) i.set(t[e], e), o(t[e]);
		let s = n.get(e.id);
		s && (s.sort((e, t) => t.start - e.start || e.end - t.end), a.push(...s));
	};
	o(e);
	let s = (e, t) => {
		let n = r.get(t.parent);
		if (!n) return !1;
		let a = r.get(e.parent);
		for (; a;) {
			if (a === n) return e.start >= t.start && e.end <= t.end;
			if (a.parent === n) {
				let e = i.get(a);
				return e !== void 0 && e >= t.start && e <= t.end;
			}
			a = a.parent;
		}
		return !1;
	}, c = /* @__PURE__ */ new Map(), l = [];
	for (let e of a) {
		let t = [];
		for (let n of l) s(n, e) && t.push(n);
		c.set(e.id, t), l.push(e);
	}
	return {
		order: a,
		contained: c
	};
}, _r = function(e, t) {
	let n = e.summaries.findIndex((e) => e.id === t);
	return n !== -1 && (e.summaries.splice(n, 1), e.nodes.querySelector("#s-" + t)?.remove(), e.nodes.querySelector("#label-s-" + t)?.remove(), !0);
}, vr = function(e, { parent: t, start: n }) {
	let r = e.findEle(t), i = r.nodeObj, a;
	return a = i.parent ? me(r.closest(".me-main")) : me(e.findEle(i.children[n].id).closest(".me-main")), a;
}, yr = function(e, t, n = [], r) {
	let { id: i, label: a, parent: o, start: s, end: c, style: l } = t, { nodes: u, theme: d, summarySvg: f } = e, p = e.findEle(o).nodeObj, m = vr(e, t), h = Infinity, g = 0, v = 0, y = 0, b = 0, x = Infinity, S = 0;
	for (let t = s; t <= c; t++) {
		let n = p.children?.[t];
		if (!n) return console.warn("Child not found"), null;
		let r = pr(e.findEle(n.id)), { offsetLeft: i, offsetTop: a } = _(u, r), o = s === c ? 10 : 20;
		t === s && (v = a + o), t === c && (y = a + r.offsetHeight - o), t === s && (x = i + o), t === c && (S = i + r.offsetWidth - o), a + r.offsetHeight > b && (b = a + r.offsetHeight), i < h && (h = i), r.offsetWidth + i > g && (g = r.offsetWidth + i);
	}
	let C = 0;
	if (n.length > 0 && r) if (m === P.DOWN) {
		let e = -Infinity;
		for (let t of n) {
			let n = r.get(t.id);
			n && n.bottom > e && (e = n.bottom);
		}
		e !== -Infinity && (C = Math.max(0, e - b + mr));
	} else if (m === P.LHS) {
		let e = Infinity;
		for (let t of n) {
			let n = r.get(t.id);
			n && n.left < e && (e = n.left);
		}
		e !== Infinity && (C = Math.max(0, h + 10 - e + mr));
	} else {
		let e = -Infinity;
		for (let t of n) {
			let n = r.get(t.id);
			n && n.right > e && (e = n.right);
		}
		e !== -Infinity && (C = Math.max(0, e - g + 10 + mr));
	}
	let w, T, E = l?.stroke || d.cssVar["--color"], D = l?.labelColor || d.cssVar["--color"], O = "s-" + i, k = e.markdown ? e.markdown(a, t) : a;
	if (m === P.DOWN) {
		let e = b + hr + C, t = (x + S) / 2;
		w = fr(`M ${x} ${e - 10} c 0 5 5 10 10 10 L ${S - 10} ${e} c 5 0 10 -5 10 -10 M ${t} ${e} v 10`, E), T = Lt(k, t, e + 20, {
			anchor: "middle",
			color: D,
			dataType: "summary",
			svgId: O
		});
	} else {
		let e = p.parent ? 10 : 0, t = v + e, n = y + e, r = (t + n) / 2;
		m === P.LHS ? (w = fr(`M ${h + 10 - C} ${t} c -5 0 -10 5 -10 10 L ${h - C} ${n - 10} c 0 5 5 10 10 10 M ${h - C} ${r} h -10`, E), T = Lt(k, h - 20 - C, r, {
			anchor: "end",
			color: D,
			dataType: "summary",
			svgId: O
		})) : (w = fr(`M ${g - 10 + C} ${t} c 5 0 10 5 10 10 L ${g + C} ${n - 10} c 0 5 -5 10 -10 10 M ${g + C} ${r} h 10`, E), T = Lt(k, g + 20 + C, r, {
			anchor: "start",
			color: D,
			dataType: "summary",
			svgId: O
		}));
	}
	let A = dr(O);
	A.appendChild(w), e.labelContainer.appendChild(T), B(T), A.summaryObj = t, A.labelEl = T, f.appendChild(A);
	let j = T.offsetWidth, M = T.offsetHeight, N;
	if (m === P.DOWN) {
		let e = b + hr + C, t = (x + S) / 2;
		N = {
			top: e - 10,
			bottom: e + 20 + M / 2,
			left: Math.min(x, t - j / 2),
			right: Math.max(S, t + j / 2)
		};
	} else if (m === P.LHS) {
		let e = p.parent ? 10 : 0, t = (v + e + y + e) / 2;
		N = {
			left: h - 20 - C - j,
			right: h - C + 10,
			top: Math.min(v + e, t - M / 2),
			bottom: Math.max(y + e, t + M / 2)
		};
	} else {
		let e = p.parent ? 10 : 0, t = (v + e + y + e) / 2;
		N = {
			left: g + C - 10,
			right: g + 20 + C + j,
			top: Math.min(v + e, t - M / 2),
			bottom: Math.max(y + e, t + M / 2)
		};
	}
	return r?.set(i, N), A;
}, br = function(e = {}) {
	let { currentNodes: t, summaries: n, bus: r } = this, i = ur(t);
	if (!i) return;
	let { parent: a, start: o, end: s } = i, c = {
		id: m(),
		parent: a,
		start: o,
		end: s,
		label: "summary",
		style: e.style
	};
	n.push(c), this.renderSummary();
	let l = this.nodes.querySelector("#s-" + c.id);
	l && this.editSummary(l), r.fire("operation", {
		name: "createSummary",
		target: c
	});
}, xr = function(e) {
	let t = m(), n = {
		...e,
		id: t
	};
	this.summaries.push(n), this.renderSummary(), this.bus.fire("operation", {
		name: "createSummary",
		target: n
	});
}, Sr = function(e) {
	let t = this.summaries.find((t) => t.id === e);
	!t || !_r(this, e) || (this.renderSummary(), this.bus.fire("operation", {
		name: "removeSummary",
		target: t
	}));
}, Cr = function(e) {
	let t = e.labelEl;
	t && t.classList.add("selected"), this.currentSummary = e, this.bus.fire("selectSummary", e.summaryObj);
}, wr = function() {
	this.currentSummary?.labelEl?.classList.remove("selected"), this.currentSummary = null, this.bus.fire("unselectSummary");
}, Tr = function() {
	if (this.summarySvg.innerHTML = "", this.labelContainer.querySelectorAll(".svg-label[data-type=\"summary\"]").forEach((e) => e.remove()), this.summaries.length === 0) {
		this.nodes.insertAdjacentElement("beforeend", this.summarySvg);
		return;
	}
	let e = [], { order: t, contained: n } = gr(this.nodeData, this.summaries), r = /* @__PURE__ */ new Map();
	for (let i of t) try {
		yr(this, i, n.get(i.id) || [], r) === null && e.push(i.id);
	} catch {
		console.warn("Node may not be expanded");
	}
	e.forEach((e) => _r(this, e)), this.nodes.insertAdjacentElement("beforeend", this.summarySvg);
}, Er = function(e) {
	e && e.labelEl && Vt(this, e.labelEl, e.summaryObj);
};
//#endregion
//#region src/methods.ts
function Dr(e, t) {
	return async function(...n) {
		let r = this.before[t];
		r && !await r.apply(this, n) || e.apply(this, n);
	};
}
var Or = Object.keys(Ee), kr = {};
for (let e = 0; e < Or.length; e++) {
	let t = Or[e];
	kr[t] = Dr(Ee[t], t);
}
var Ar = {
	getObjById: l,
	generateNewObj: h,
	layout: ie,
	linkDiv: Ut,
	editTopic: ge,
	createWrapper: le,
	createParent: ue,
	createChildren: de,
	createTopic: fe,
	findEle: se,
	changeTheme: zn,
	changeCompact: Bn,
	...Ue,
	...kr,
	...Hn,
	...lr,
	async init(e) {
		if (!this.pluginsInitialized) {
			if (e = JSON.parse(JSON.stringify(e)), !e || !e.nodeData) return /* @__PURE__ */ Error("MindElixir: `data` is required");
			e.direction !== void 0 && (this.direction = e.direction), e.compact !== void 0 && (this.compact = e.compact), this.changeTheme(e.theme || this.theme, !1), e.meta && (this.meta = e.meta), this.nodeData = e.nodeData, u(this.nodeData), this.arrows = e.arrows || [], this.summaries = e.summaries || [], this.tidyArrow(), this.container.style.opacity = "0", this.layout(), await document.fonts.ready, this.container && (this.linkDiv(), this.toCenter(), this.container.style.opacity = "", this.toolBar && this.disposable.push(vn(this)), this.keypress && Pt(this, this.keypress), Fn(this), this.disposable.push(re(this)), this.contextMenu && this.disposable.push(Kt(this, this.contextMenu)), dn(this), this.allowUndo && this.disposable.push(mn(this)), this.pluginsInitialized = !0);
		}
	},
	destroy() {
		this.pluginsInitialized = !0;
		let e = this.disposable || [];
		this.disposable = [], e.forEach((e) => e()), this.helper1?.destroy?.(), this.helper2?.destroy?.(), this.el && (this.el.innerHTML = ""), this.el = void 0, this.nodeData = void 0, this.arrows = void 0, this.summaries = void 0, this.currentArrow = void 0, this.currentNodes = void 0, this.currentSummary = void 0, this.theme = void 0, this.direction = void 0, this.bus = void 0, this.container = void 0, this.map = void 0, this.lines = void 0, this.linkController = void 0, this.arrowSvg = void 0, this.P2 = void 0, this.P3 = void 0, this.line1 = void 0, this.line2 = void 0, this.nodes = void 0, this.root = void 0, this.summarySvg = void 0, this.labelContainer = void 0, this.dragged = null, this.nodeDataBackup = void 0, this.meta = void 0, this.panHelper = void 0, this.helper1 = void 0, this.helper2 = void 0, this.historyStack = void 0, this.selection?.destroy(), this.selection = void 0;
	},
	enableMobileMultiSelect(e) {
		this.mobileMultiSelect = e;
	}
}, jr = "6.0.0";
//#endregion
//#region src/utils/panHelper.ts
function Mr(e) {
	return {
		x: 0,
		y: 0,
		moved: !1,
		mousedown: !1,
		handlePointerDown(t) {
			this.moved = !1;
			let n = t.target, r = e.mouseSelectionButton === 0 ? 2 : 0, i = e.spacePressed && t.button === 0 && t.pointerType === "mouse", a = !e.editable || t.button === r && t.pointerType === "mouse" || t.pointerType === "touch";
			!i && !a || (this.x = t.clientX, this.y = t.clientY, n.className !== "circle" && n.contentEditable !== "plaintext-only" && (this.mousedown = !0, n.setPointerCapture(t.pointerId)));
		},
		handlePointerMove(t) {
			if (!this.mousedown || t.target.contentEditable === "plaintext-only" && !e.spacePressed) return !1;
			let n = t.clientX - this.x, r = t.clientY - this.y;
			return this.x = t.clientX, this.y = t.clientY, this.moved = !0, e.move(n, r), !0;
		},
		handlePointerUp(e) {
			if (!this.mousedown) return;
			let t = e.target;
			t.hasPointerCapture && t.hasPointerCapture(e.pointerId) && t.releasePointerCapture(e.pointerId), this.mousedown = !1;
		},
		clear() {
			this.mousedown = !1, this.moved = !1;
		}
	};
}
//#endregion
//#region src/outliner/icons.ts
var Nr = {
	home: "<path d=\"M3 9.5 12 3l9 6.5\"/><path d=\"M5 10v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V10\"/><path d=\"M9 21v-6h6v6\"/>",
	ellipsis: "<circle cx=\"12\" cy=\"12\" r=\"1\"/><circle cx=\"19\" cy=\"12\" r=\"1\"/><circle cx=\"5\" cy=\"12\" r=\"1\"/>",
	chevronDown: "<path d=\"m6 9 6 6 6-6\"/>",
	chevronRight: "<path d=\"m9 18 6-6-6-6\"/>",
	arrowLeft: "<path d=\"m12 19-7-7 7-7\"/><path d=\"M19 12H5\"/>",
	arrowRight: "<path d=\"M5 12h14\"/><path d=\"m12 5 7 7-7 7\"/>",
	trash: "<path d=\"M3 6h18\"/><path d=\"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6\"/><path d=\"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2\"/><path d=\"M10 11v6\"/><path d=\"M14 11v6\"/>"
}, Pr = (e, t) => `<svg xmlns="http://www.w3.org/2000/svg" width="${t}" height="${t}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${Nr[e] ?? ""}</svg>`, Fr = /* @__PURE__ */ new Map();
function $(e, t = 16) {
	let n = `${e}:${t}`, r = Fr.get(n);
	return r === void 0 && (r = Pr(e, t), Fr.set(n, r)), r;
}
//#endregion
//#region src/outliner/types.ts
var Ir = {
	menuTitle: "操作菜单",
	outdent: "取消缩进",
	indent: "缩进",
	delete: "删除",
	untitled: "(无标题)",
	zoomInAndDrag: "点击进入 / 拖拽移动"
}, Lr = (e) => {
	e.children ||= [], e.children.forEach(Lr);
}, Rr = class {
	el;
	breadcrumbEl;
	itemsEl;
	root;
	history;
	mei;
	suppressSync = !1;
	syncDirty = !1;
	syncQueued = !1;
	readonly;
	markdown;
	i18n;
	fileName;
	onChange;
	zoomedId = null;
	editingId = null;
	compositionJustEnded = !1;
	openMenuId = null;
	draggedId = null;
	draggedContainer = null;
	dropIndicator = null;
	views = /* @__PURE__ */ new Map();
	seen = /* @__PURE__ */ new Set();
	breadcrumbSig = "";
	disposers = [];
	constructor(e) {
		let t = typeof e.el == "string" ? document.querySelector(e.el) : e.el;
		if (!t) throw Error("Outliner: el is not a valid element");
		if (this.el = t, this.el.innerHTML = "", this.mei = e.mei, !this.mei.historyStack) throw Error("Outliner: mei.historyStack is missing — create the MindElixir instance with `allowUndo: true` and await `init`");
		this.history = this.mei.historyStack, this.readonly = e.readonly ?? !1, this.markdown = e.markdown, this.i18n = {
			...Ir,
			...e.i18n
		}, this.fileName = e.fileName, this.onChange = e.onChange, this.bindRoot(), this.breadcrumbEl = document.createElement("div"), this.breadcrumbEl.className = "outliner-breadcrumb", this.itemsEl = document.createElement("div"), this.itemsEl.className = "outliner-items";
		let n = document.createElement("div");
		n.className = "outliner-container", n.appendChild(this.breadcrumbEl), n.appendChild(this.itemsEl), this.el.appendChild(n), this.disposers.push(this.history.subscribe(this.requestSync));
		let r = (e) => {
			e.silent && this.scheduleSync();
		};
		this.mei.bus.addListener("operation", r), this.disposers.push(() => this.mei.bus.removeListener("operation", r)), document.addEventListener("keydown", this.handleGlobalKeydown), this.disposers.push(() => document.removeEventListener("keydown", this.handleGlobalKeydown)), document.addEventListener("mousedown", this.handleDocumentMousedown), this.disposers.push(() => document.removeEventListener("mousedown", this.handleDocumentMousedown)), this.el.addEventListener("keydown", this.handleTopicKeydown), this.el.addEventListener("compositionend", this.handleCompositionEnd), this.disposers.push(() => this.el.removeEventListener("compositionend", this.handleCompositionEnd)), this.el.addEventListener("click", this.handleClick), this.el.addEventListener("focusin", this.handleFocusIn), this.el.addEventListener("focusout", this.handleFocusOut), this.el.addEventListener("dragstart", this.handleDragStart), this.el.addEventListener("dragend", this.handleDragEnd), this.el.addEventListener("dragover", this.handleDragOver), this.el.addEventListener("dragleave", this.handleDragLeave), this.el.addEventListener("drop", this.handleDrop), this.render();
	}
	getData() {
		return JSON.parse(this.mei.stringifyData(this.root));
	}
	addChild(e) {
		let t = this.meiEle(e);
		if (!t) return;
		this.flushEditingText();
		let n = m();
		this.mei.addChild(t, {
			id: n,
			topic: "",
			children: []
		}), this.focusItem(n);
	}
	destroy() {
		this.disposers.forEach((e) => e()), this.disposers = [], this.el.removeEventListener("keydown", this.handleTopicKeydown), this.el.removeEventListener("keydown", this.handleGlobalKeydown), this.el.removeEventListener("click", this.handleClick), this.el.removeEventListener("focusin", this.handleFocusIn), this.el.removeEventListener("focusout", this.handleFocusOut), this.el.removeEventListener("dragstart", this.handleDragStart), this.el.removeEventListener("dragend", this.handleDragEnd), this.el.removeEventListener("dragover", this.handleDragOver), this.el.removeEventListener("dragleave", this.handleDragLeave), this.el.removeEventListener("drop", this.handleDrop), this.views.clear(), this.seen.clear(), this.dropIndicator = null, this.draggedContainer = null, this.syncDirty = !1, this.el.innerHTML = "";
	}
	focusItem(e) {
		let t = this.itemsEl.querySelector(`[data-outline-item][data-item-id="${CSS.escape(e)}"]`);
		if (!t) return;
		let n = document.activeElement === t;
		t.focus(), n && this.placeCaretAtEnd(t);
	}
	bindRoot() {
		let e = this.mei.nodeData;
		this.root !== e && (this.root = e), Lr(e);
	}
	byId(e) {
		return l(e, this.root);
	}
	isRoot(e) {
		return this.root.id === e;
	}
	parentOf(e) {
		return this.byId(e)?.parent ?? null;
	}
	prevSiblingOf(e) {
		let t = this.byId(e), n = t?.parent?.children;
		if (!t || !n) return null;
		let r = n.indexOf(t);
		return r > 0 ? n[r - 1] : null;
	}
	pathTo(e) {
		let t = [], n = this.byId(e);
		for (; n && (t.unshift({
			id: n.id,
			topic: n.topic
		}), n.id !== this.root.id);) n = n.parent ?? null;
		return t;
	}
	meiEle(e) {
		try {
			return this.mei.findEle(e);
		} catch {
			return null;
		}
	}
	requestSync = () => {
		this.suppressSync || (this.syncDirty = !1, this.rerenderFromMei());
	};
	scheduleSync = () => {
		this.suppressSync || (this.syncDirty = !0, !this.syncQueued && (this.syncQueued = !0, queueMicrotask(() => {
			this.syncQueued = !1, this.syncDirty && (this.syncDirty = !1, this.rerenderFromMei());
		})));
	};
	rerenderFromMei() {
		this.suppressSync || (this.bindRoot(), this.zoomedId && !this.byId(this.zoomedId) && (this.zoomedId = null), this.editingId = null, this.openMenuId = null, this.render(), this.emitChange());
	}
	emitChange() {
		this.onChange?.(this.getData());
	}
	flushEditingText() {
		let e = this.liveEditingText();
		if (!e) return;
		let t = this.byId(e.id);
		t && t.topic !== e.text && this.setNodeTopicBound(e.id, e.text);
	}
	setNodeTopicBound(e, t) {
		let n = this.meiEle(e);
		if (n) {
			this.suppressSync = !0;
			try {
				this.mei.reshapeNode(n, { topic: t });
			} finally {
				this.suppressSync = !1;
			}
		}
	}
	expandBound(e, t) {
		let n = this.meiEle(e);
		n && this.mei.expandNode(n, t);
	}
	applyOperation(e) {
		if (this.readonly || this.isRoot(e.id)) return;
		this.flushEditingText();
		let t = this.meiEle(e.id);
		if (!t) return;
		let n = e.type === "addSibling" || e.type === "addSiblingBefore" ? m() : null, r = n ? {
			id: n,
			topic: e.newNodeContent ?? "",
			children: []
		} : void 0;
		switch (e.type) {
			case "addSibling":
				this.mei.insertSibling("after", t, r);
				break;
			case "addSiblingBefore":
				this.mei.insertSibling("before", t, r);
				break;
			case "indent": {
				let n = this.prevSiblingOf(e.id), r = n ? this.meiEle(n.id) : null;
				r && this.mei.moveNodesIn([t], r);
				break;
			}
			case "outdent": {
				let n = this.parentOf(e.id), r = n && !this.isRoot(n.id) ? this.meiEle(n.id) : null;
				r && this.mei.moveNodesAfter([t], r);
				break;
			}
			case "moveUp":
				this.mei.moveUpNode(t);
				break;
			case "moveDown":
				this.mei.moveDownNode(t);
				break;
			case "moveTo": {
				let n = e.targetId ? this.meiEle(e.targetId) : null;
				if (!n || this.isRoot(e.targetId) && e.dropPosition !== "inside") break;
				e.dropPosition === "before" ? this.mei.moveNodesBefore([t], n) : e.dropPosition === "after" ? this.mei.moveNodesAfter([t], n) : this.mei.moveNodesIn([t], n);
				break;
			}
		}
		n ? this.focusItem(n) : e.shouldFocusCurrent && this.focusItem(e.id);
	}
	deleteItem(e) {
		if (this.readonly || this.isRoot(e)) return;
		let t = this.getTopicEl(e), n = null;
		if (t) {
			let r = Array.from(this.itemsEl.querySelectorAll("[data-outline-item]")), i = r.indexOf(t);
			n = i > 0 ? r[i - 1].getAttribute("data-item-id") : this.parentOf(e)?.id ?? null;
		}
		this.flushEditingText();
		let r = this.meiEle(e);
		r && (this.mei.removeNodes([r]), n && this.focusItem(n));
	}
	render() {
		this.zoomedId && !this.byId(this.zoomedId) && (this.zoomedId = null), this.renderBreadcrumb();
		let e = this.zoomedId ? this.byId(this.zoomedId) : null, t = e ? e.children : [this.root];
		this.seen.clear();
		let n = null;
		for (let e of t) n = this.syncItem(e, 0, this.zoomedId ?? void 0, t.length, this.itemsEl, n);
		this.unmountUnseen();
	}
	renderBreadcrumb() {
		let e = this.zoomedId ? this.pathTo(this.zoomedId) : [], t = `${this.fileName ?? ""}\u0000${e.map((e) => `${e.id}:${e.topic}`).join("\0")}`;
		if (t === this.breadcrumbSig) return;
		this.breadcrumbSig = t, this.breadcrumbEl.innerHTML = "";
		let n = document.createElement("button");
		n.className = "breadcrumb-item breadcrumb-root", n.innerHTML = `${$("home")}<span class="breadcrumb-text">${this.escapeText(this.fileName ?? "")}</span>`, n.addEventListener("click", () => this.zoomTo(null)), this.breadcrumbEl.appendChild(n), e.forEach((t, n) => {
			let r = document.createElement("span");
			r.className = "breadcrumb-segment";
			let i = n === e.length - 1, a = this.escapeText(t.topic || this.i18n.untitled);
			if (i) r.innerHTML = `<span class="breadcrumb-separator">/</span><span class="breadcrumb-item breadcrumb-current">${a}</span>`;
			else {
				let e = document.createElement("button");
				e.className = "breadcrumb-item", e.innerHTML = a, e.addEventListener("click", () => this.zoomTo(t.id)), r.innerHTML = "<span class=\"breadcrumb-separator\">/</span>", r.appendChild(e);
			}
			this.breadcrumbEl.appendChild(r);
		});
	}
	syncItem(e, t, n, r, i, a) {
		let o = this.views.get(e.id);
		o ? this.patchItemView(o, e, t, n, r) : (o = this.createItemView(e, t, n, r), this.views.set(e.id, o));
		let s = a ? a.nextSibling : i.firstChild;
		if (s !== o.container && i.insertBefore(o.container, s), this.seen.add(e.id), e.expanded !== !1) {
			let n = o.wrapper;
			for (let r of e.children) n = this.syncItem(r, t + 1, e.id, e.children.length, o.container, n);
		}
		return o.container;
	}
	unmountUnseen() {
		for (let [e, t] of this.views) this.seen.has(e) || (t.container.remove(), this.views.delete(e), this.openMenuId === e && (this.openMenuId = null));
	}
	createItemView(e, t, n, r) {
		let i = document.createElement("div");
		i.className = "outline-item-container", i.dataset.itemId = e.id, this.readonly && (i.style.pointerEvents = "none");
		let a = null;
		t > 0 && (a = document.createElement("div"), a.className = "outline-item-vertical-line", a.style.left = `${t * 24 - 13}px`, a.style.height = "100%", i.appendChild(a));
		let o = document.createElement("div");
		o.className = "outline-item-wrapper", o.dataset.itemId = e.id, o.style.marginLeft = `${t * 24}px`, i.appendChild(o);
		let s = document.createElement("div");
		s.className = "outline-item-front";
		let c = document.createElement("div");
		c.className = `outline-item-dot${this.readonly ? "" : " outline-item-dot-zoomable"}`, c.title = this.i18n.zoomInAndDrag, this.readonly || (c.draggable = !0), s.appendChild(c), o.appendChild(s);
		let l = document.createElement("div");
		l.className = "outline-item-topic", l.dataset.outlineItem = "", l.dataset.itemId = e.id, this.readonly || (l.contentEditable = "plaintext-only"), this.writeTopicHtml(l, e.topic, e), o.appendChild(l);
		let u = document.createElement("div");
		u.className = "outline-item-btn-group";
		let d = null, f = null;
		this.readonly || (d = document.createElement("div"), d.className = "outline-item-menu-wrapper", f = document.createElement("button"), f.className = "outline-item-menu-btn", f.title = this.i18n.menuTitle, f.draggable = !1, f.innerHTML = $("ellipsis", 12), d.appendChild(f), u.appendChild(d));
		let p = document.createElement("button");
		return p.className = "outline-item-collapse-btn", p.dataset.state = e.children.length === 0 ? "hidden" : e.expanded === !1 ? "collapsed" : "expanded", p.innerHTML = $(e.expanded === !1 ? "chevronRight" : "chevronDown"), u.appendChild(p), o.appendChild(u), {
			container: i,
			wrapper: o,
			line: a,
			dot: c,
			topic: l,
			btnGroup: u,
			menuWrapper: d,
			menuBtn: f,
			dropdown: null,
			menuOpen: !1,
			collapse: p,
			topicText: e.topic,
			topicDirty: !1,
			item: e,
			level: t,
			parentId: n,
			siblingCount: r
		};
	}
	patchItemView(e, t, n, r, i) {
		let a = e.level !== n;
		e.item = t, e.level = n, e.parentId = r, e.siblingCount = i, a && (e.wrapper.style.marginLeft = `${n * 24}px`, e.line && (e.line.style.left = `${n * 24 - 13}px`)), this.editingId !== t.id && (e.topicDirty || e.topicText !== t.topic) && (this.writeTopicHtml(e.topic, t.topic, t), e.topicText = t.topic, e.topicDirty = !1);
		let o = t.children.length === 0 ? "hidden" : t.expanded === !1 ? "collapsed" : "expanded";
		e.collapse.dataset.state !== o && (e.collapse.dataset.state = o, e.collapse.innerHTML = $(t.expanded === !1 ? "chevronRight" : "chevronDown")), this.syncDropdown(e);
	}
	syncDropdown(e) {
		let t = !!e.menuWrapper && this.openMenuId === e.item.id;
		t && !e.dropdown ? (e.dropdown = this.createDropdown(e), e.menuWrapper.appendChild(e.dropdown)) : !t && e.dropdown && (e.dropdown.remove(), e.dropdown = null), e.menuOpen !== t && (e.wrapper.classList.toggle("menu-open", t), e.menuOpen = t);
	}
	createDropdown(e) {
		let t = document.createElement("div");
		t.className = "outline-item-menu-dropdown";
		let n = (e, n, r, i = !1) => {
			let a = document.createElement("button");
			a.className = `outline-item-menu-item${i ? " outline-item-menu-item-danger" : ""}`, a.dataset.action = r, a.innerHTML = `${$(n, 12)}<span>${e}</span>`, t.appendChild(a);
		};
		return n(this.i18n.outdent, "arrowLeft", "outdent"), n(this.i18n.indent, "arrowRight", "indent"), (e.level > 0 || e.siblingCount > 1) && n(this.i18n.delete, "trash", "delete", !0), t;
	}
	toggleMenu(e) {
		this.setOpenMenu(this.openMenuId === e ? null : e);
	}
	setOpenMenu(e) {
		let t = this.openMenuId;
		if (t !== e) {
			if (this.openMenuId = e, t) {
				let e = this.views.get(t);
				e && this.syncDropdown(e);
			}
			if (e) {
				let t = this.views.get(e);
				t && this.syncDropdown(t);
			}
		}
	}
	runMenuAction(e) {
		let t = this.openMenuId;
		if (!t) return;
		let n = this.views.get(t);
		if (!n) return;
		let { item: r, level: i, siblingCount: a } = n;
		this.setOpenMenu(null), e === "outdent" ? this.applyOperation({
			type: "outdent",
			id: r.id,
			shouldFocusCurrent: !0
		}) : e === "indent" ? this.applyOperation({
			type: "indent",
			id: r.id,
			shouldFocusCurrent: !0
		}) : e === "delete" && (i > 0 || a > 1) && this.deleteItem(r.id);
	}
	handleDragStart = (e) => {
		let t = e.target;
		if (!t.closest?.(".outline-item-dot")) return;
		let n = t.closest(".outline-item-container"), r = n?.dataset.itemId;
		!n || !r || (e.stopPropagation(), this.draggedId = r, this.draggedContainer = n, e.dataTransfer && (e.dataTransfer.effectAllowed = "move"), n.style.opacity = "0.4");
	};
	handleDragEnd = () => {
		this.clearDropIndicator(), this.draggedId = null, this.draggedContainer &&= (this.draggedContainer.style.opacity = "", null);
	};
	handleDragOver = (e) => {
		let t = e.target.closest?.(".outline-item-wrapper");
		if (!t) return;
		e.stopPropagation(), e.preventDefault();
		let n = () => t.classList.remove("drag-over", "drag-over-bottom", "drag-over-inside"), r = this.views.get(t.dataset.itemId ?? "");
		if (!r || !this.draggedId || this.draggedId === r.item.id) {
			n();
			return;
		}
		let i = t.closest(".outline-item-container");
		if (!this.draggedContainer || !i || this.draggedContainer.contains(i)) {
			n(), e.dataTransfer && (e.dataTransfer.dropEffect = "none");
			return;
		}
		e.dataTransfer && (e.dataTransfer.dropEffect = "move");
		let a = t.getBoundingClientRect(), o = e.clientY - a.top, s = o < a.height * .25 ? "before" : o > a.height * .75 ? "after" : "inside";
		(this.dropIndicator?.el !== t || this.dropIndicator.position !== s) && (this.clearDropIndicator(), t.classList.add(s === "before" ? "drag-over" : s === "after" ? "drag-over-bottom" : "drag-over-inside"), this.dropIndicator = {
			el: t,
			position: s
		});
	};
	handleDragLeave = (e) => {
		let t = e.target.closest?.(".outline-item-wrapper");
		t && (e.stopPropagation(), t.contains(e.relatedTarget) || t.classList.remove("drag-over", "drag-over-bottom", "drag-over-inside"));
	};
	handleDrop = (e) => {
		let t = e.target.closest?.(".outline-item-wrapper");
		if (!t) return;
		e.preventDefault(), e.stopPropagation();
		let n = this.dropIndicator?.el === t ? this.dropIndicator.position : null;
		this.clearDropIndicator();
		let r = this.views.get(t.dataset.itemId ?? ""), i = this.draggedId;
		!r || !i || i === r.item.id || !n || this.applyOperation({
			type: "moveTo",
			id: i,
			targetId: r.item.id,
			dropPosition: n,
			shouldFocusCurrent: !0
		});
	};
	clearDropIndicator() {
		this.dropIndicator &&= (this.dropIndicator.el.classList.remove("drag-over", "drag-over-bottom", "drag-over-inside"), null);
	}
	writeTopicHtml(e, t, n) {
		this.markdown ? e.innerHTML = this.markdown(t, n) : e.textContent = t;
	}
	escapeText(e) {
		let t = document.createElement("div");
		return t.textContent = e, t.innerHTML;
	}
	getTopicEl(e) {
		return this.itemsEl.querySelector(`[data-outline-item][data-item-id="${CSS.escape(e)}"]`);
	}
	liveEditingText() {
		if (!this.editingId) return null;
		let e = this.getTopicEl(this.editingId);
		return e ? {
			id: this.editingId,
			text: e.textContent ?? ""
		} : null;
	}
	handleFocusIn = (e) => {
		let t = e.target;
		if (!t.matches?.("[data-outline-item]")) return;
		let n = t.getAttribute("data-item-id"), r = this.byId(n);
		if (!r) return;
		this.editingId = n, t.textContent = r.topic;
		let i = this.views.get(n);
		i && (i.topicDirty = !0), this.placeCaretAtEnd(t);
	};
	placeCaretAtEnd(e) {
		let t = document.createRange();
		t.selectNodeContents(e), t.collapse(!1);
		let n = window.getSelection();
		n?.removeAllRanges(), n?.addRange(t);
	}
	markTopicClean(e, t) {
		let n = this.views.get(e);
		n && (n.topicText = t, n.topicDirty = !1);
	}
	handleFocusOut = (e) => {
		let t = e.target;
		if (!t.matches?.("[data-outline-item]")) return;
		let n = t.getAttribute("data-item-id");
		if (this.editingId !== n) return;
		this.editingId = null;
		let r = t.textContent ?? "", i = this.byId(n);
		i && i.topic !== r && this.setNodeTopicBound(n, r);
		let a = this.byId(n);
		a && this.writeTopicHtml(t, a.topic, a), this.markTopicClean(n, a?.topic ?? r);
	};
	handleCompositionEnd = () => {
		this.compositionJustEnded = !0, setTimeout(() => {
			this.compositionJustEnded = !1;
		}, 0);
	};
	handleTopicKeydown = (e) => {
		if (e.isComposing || e.keyCode === 229 || this.compositionJustEnded && (e.key === "Enter" || e.key === "Escape")) return;
		let t = e.target.closest?.("[data-outline-item]");
		if (!t || this.readonly) return;
		let n = t.getAttribute("data-item-id"), r = t.textContent?.trim();
		if (e.key === "ArrowUp" && e.altKey) e.preventDefault(), this.applyOperation({
			type: "moveUp",
			id: n,
			shouldFocusCurrent: !0
		});
		else if (e.key === "ArrowDown" && e.altKey) e.preventDefault(), this.applyOperation({
			type: "moveDown",
			id: n,
			shouldFocusCurrent: !0
		});
		else if (e.key === "ArrowUp" || e.key === "ArrowDown") {
			e.preventDefault();
			let n = Array.from(this.itemsEl.querySelectorAll("[data-outline-item]")), r = n.indexOf(t);
			if (r === -1) return;
			let i = n[r + (e.key === "ArrowUp" ? -1 : 1)];
			i && (t.blur(), i.focus());
		} else if (e.key === "Enter") {
			if (e.preventDefault(), e.shiftKey) {
				this.applyOperation({
					type: "addSiblingBefore",
					id: n
				});
				return;
			}
			let r = t.textContent ?? "", i = window.getSelection(), a = r.length;
			if (i && i.rangeCount > 0) {
				let e = i.getRangeAt(0), n = e.cloneRange();
				n.selectNodeContents(t), n.setEnd(e.endContainer, e.endOffset), a = n.toString().length;
			}
			let o = r.substring(0, a), s = r.substring(a);
			if (o.trim() === "" && s.trim() === "") this.applyOperation({
				type: "outdent",
				id: n,
				shouldFocusCurrent: !0
			});
			else if (s.trim() !== "") {
				let e = this.meiEle(n);
				if (!e) return;
				let t = m();
				o !== (this.byId(n)?.topic ?? "") && this.setNodeTopicBound(n, o), this.mei.insertSibling("after", e, {
					id: t,
					topic: s,
					children: []
				}), this.focusItem(t);
			} else this.applyOperation({
				type: "addSibling",
				id: n
			});
		} else e.key === "Tab" ? (e.preventDefault(), this.applyOperation({
			type: e.shiftKey ? "outdent" : "indent",
			id: n,
			shouldFocusCurrent: !0
		})) : e.key === "Backspace" && r === "" && !this.isRoot(n) && (e.preventDefault(), this.deleteItem(n));
	};
	handleClick = (e) => {
		let t = e.target;
		if (!t.closest || t.closest(".breadcrumb-item")) return;
		let n = t.closest(".outline-item-container")?.dataset.itemId, r = t.closest(".outline-item-menu-item");
		if (r) {
			e.stopPropagation(), this.runMenuAction(r.dataset.action ?? "");
			return;
		}
		if (t.closest(".outline-item-menu-btn")) {
			e.stopPropagation(), n && this.toggleMenu(n);
			return;
		}
		if (t.closest(".outline-item-collapse-btn")) {
			e.stopPropagation();
			let t = n ? this.views.get(n) : void 0;
			t && this.expandBound(t.item.id, t.item.expanded === !1);
			return;
		}
		if (t.closest(".outline-item-dot")) {
			e.stopPropagation(), n && this.zoomTo(n);
			return;
		}
		this.setOpenMenu(null);
	};
	handleDocumentMousedown = (e) => {
		this.openMenuId && (e.target.closest?.(".outline-item-menu-wrapper") || this.setOpenMenu(null));
	};
	handleGlobalKeydown = (e) => {
		if (this.mei.container?.contains(e.target)) return;
		let t = document.activeElement, n = !!t && (t.getAttribute("contenteditable") === "true" || t.isContentEditable), r = !!t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA"), i = e.metaKey || e.ctrlKey, a = e.key.toLowerCase();
		if (n && i && a === "z" && !e.shiftKey) {
			let e = t.textContent || "", n = !1;
			try {
				n = document.execCommand("undo");
			} catch {
				n = !1;
			}
			setTimeout(() => {
				let r = t.textContent || "";
				(!n || e === r) && (t.blur(), this.mei.undo());
			}, 0);
			return;
		}
		r || n || (i && a === "z" && !e.shiftKey ? (e.preventDefault(), this.mei.undo()) : i && (a === "y" || a === "z" && e.shiftKey) && (e.preventDefault(), this.mei.redo()));
	};
	zoomTo(e) {
		this.setOpenMenu(null), this.zoomedId = e, this.syncDirty = !1, this.render();
	}
}, zr = class {
	static LEFT = 0;
	static RIGHT = 1;
	static SIDE = 2;
	static DOWN = 3;
	static THEME = o;
	static DARK_THEME = s;
	static version = jr;
	static E = se;
	static new = (e) => ({ nodeData: {
		id: m(),
		topic: e || "new topic",
		children: []
	} });
	get currentNode() {
		return this.currentNodes[this.currentNodes.length - 1];
	}
	constructor({ el: e, direction: t, rtl: n, editable: r, contextMenu: i, toolBar: a, keypress: c, mouseSelectionButton: l, selectionContainer: u, before: d, newTopicName: f, allowUndo: p, generateMainBranch: m, generateSubBranch: h, overflowHidden: g, compact: _, theme: v, alignment: y, scaleSensitivity: b, scaleMax: x, scaleMin: S, handleWheel: C, markdown: w, imageProxy: T, pasteHandler: E, mobileMultiSelect: D }) {
		let O = null, k = Object.prototype.toString.call(e);
		if (k === "[object HTMLDivElement]" ? O = e : k === "[object String]" && (O = document.querySelector(e)), !O) throw Error("MindElixir: el is not a valid element");
		O.style.position = "relative", O.innerHTML = "", this.el = O, this.disposable = [], this.pluginsInitialized = !1, this.before = d || {}, this.newTopicName = f || "New Node", this.contextMenu = i ?? !0, this.toolBar = a ?? !0, this.keypress = c ?? !0, this.mouseSelectionButton = l ?? 0, this.direction = t ?? 1, this.rtl = n ?? !1, this.editable = r ?? !0, this.allowUndo = p ?? !0, this.scaleSensitivity = b ?? .1, this.scaleMax = x ?? 1.4, this.scaleMin = S ?? .2, this.generateMainBranch = m || Ln, this.generateSubBranch = h || Rn, this.overflowHidden = g ?? !1, this.compact = _ ?? !1, this.alignment = y ?? "root", this.handleWheel = C ?? !0, this.markdown = w || void 0, this.imageProxy = T || void 0, this.currentNodes = [], this.currentArrow = null, this.scaleVal = 1, this.tempDirection = null, this.mobileMultiSelect = D ?? !1, this.panHelper = Mr(this), this.bus = It(), this.container = document.createElement("div"), this.selectionContainer = u || this.container, this.container.className = this.rtl ? "map-container rtl" : "map-container";
		let A = window.matchMedia("(prefers-color-scheme: dark)");
		this.theme = v || (A.matches ? s : o);
		let j = document.createElement("div");
		j.className = "map-canvas", this.map = j, this.container.setAttribute("tabindex", "0"), this.container.appendChild(this.map), this.el.appendChild(this.container), this.nodes = document.createElement("div"), this.nodes.className = "me-nodes", this.lines = V("lines"), this.summarySvg = V("summary"), this.linkController = V("linkcontroller"), this.P2 = document.createElement("div"), this.P3 = document.createElement("div"), this.P2.className = this.P3.className = "circle", this.P2.style.display = this.P3.style.display = "none", this.line1 = zt(), this.line2 = zt(), this.linkController.appendChild(this.line1), this.linkController.appendChild(this.line2), this.arrowSvg = V("topiclinks"), this.labelContainer = document.createElement("div"), this.labelContainer.className = "label-container", this.map.appendChild(this.nodes), this.overflowHidden ? this.container.style.overflow = "hidden" : this.disposable.push(Ft(this)), E && (this.pasteHandler = E);
	}
};
Object.assign(zr.prototype, Ar);
//#endregion
export { s as DARK_THEME, a as DOWN, fn as HistoryStack, n as LEFT, Rr as Outliner, r as RIGHT, i as SIDE, o as THEME, zr as default, m as generateUUID };

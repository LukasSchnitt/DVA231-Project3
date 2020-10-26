$('.nav ul li').click(function(){
	$(this).addClass("active-tab").siblings().removeClass('active-tab')
})

const tabbutton = document.querySelectorAll('.nav ul li');
const tab = document.querySelectorAll('.tab');

function  navtab(panelIndex){
	tab.forEach(function(node){
		node.style.display = 'none';	
	});
	tab[panelIndex].style.display = 'block';
	
}
navtab(0);

let userbio = document.querySelector('.bio');

function bioText(){
	userbio.oldText= userbio.innerText;
	userbio.innerText = userbio.innerText.substring(0,150) + "...";
	userbio.innerHTML += '<span onclick="addLength()" id="see-more"  > See more</span>';
	
	
}
bioText();

function addLength(){
	userbio.innerHTML= userbio.oldText;
	userbio.innerHTML += '<span onclick="bioText()" id="see-less"  > See less</span>';
	
}
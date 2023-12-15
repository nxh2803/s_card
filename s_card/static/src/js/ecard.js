// alert(WURFL.form_factor);
// alert(WURFL.complete_device_name);
// action: 'add-contact',
// alert('a');
// console.log(navigator.connection);
// var log = {
	// userid: userid,
	// sessionid: sessionid,
	// mobile: (!WURFL.is_mobile)?0:1,
	// device: WURFL.form_factor,
	// device_name: WURFL.complete_device_name,
	// screen_width: screen.width,
	// screen_height: screen.height,
	// browser_info: navigator.userAgent,
	// browser_width: window.innerWidth,
	// browser_height: window.innerHeight,
// };
// $.post('https://analytic.ecard.vn/api/analytic/traffic/action/visit', log, function(data){
	// window.location = contact.attr('data-url');
// });

/* COPY */
$(document).on('click', '.content-copy', function(){
	let content = $(this);
	navigator.clipboard.writeText(content.attr('data-content'));
	alert('Content copied: ' + content.attr('data-content'));
	return false;
});

$(document).on('click', '.input-copy', function(){
	let input = $(this);
	navigator.clipboard.writeText(input.val());
	alert('Content copied: ' + input.val());
	return false;
});

$(document).on('click', '#share', function(){
	let button = $(this);
	if(navigator.share){
		navigator.share({
			title: 'SCard.vn',
			text: button.attr('data-sapo'),
			url: button.attr('data-url'),
		})
		.then(() => console.log('Sharing the success'))
		.catch((error) => console.log('Lỗi chia sẻ', error));
	}
	else{
		alert('Sharing is not supported on this browser, do it the old way.');
	}
	return false;
});
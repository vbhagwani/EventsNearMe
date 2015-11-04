var toReload = false;

// This is called with the results from from FB.getLoginStatus().
  function statusChangeCallback(response) {
    console.log('statusChangeCallback');
    console.log(response);
    // The response object is returned with a status field that lets the
    // app know the current login status of the person.
    // Full docs on the response object can be found in the documentation
    // for FB.getLoginStatus().
    if (response.status === 'connected') {
      // Logged into your app and Facebook.

      //MAKE CALL TO DATABASE W/ USER INFO
      loginSuccess();
    } else if (response.status === 'not_authorized') {
      // The person is logged into Facebook, but not your app.
     console.log('Please log into this app.');
     logoutSuccess();
    } else {
      // The person is not logged into Facebook, so we're not sure if
      // they are logged into this app or not.
      console.log('Please log into Facebook.');
      logoutSuccess();
    }
    //location.reload();
  }

  // This function is called when someone finishes with the Login
  // Button.  See the onlogin handler attached to it in the sample
  // code below.
  function checkLoginState() {
    console.log("checkLoginState");
    FB.getLoginStatus(function(response) {
      statusChangeCallback(response);
    });
  }

  window.fbAsyncInit = function() {
  FB.init({
    appId      : '1055849787782314',
    cookie     : true,  // enable cookies to allow the server to access
                        // the session
    xfbml      : true,  // parse social plugins on this page
    version    : 'v2.2' // use version 2.2
  });

  // Now that we've initialized the JavaScript SDK, we call
  // FB.getLoginStatus().  This function gets the state of the
  // person visiting this page and can return one of three states to
  // the callback you provide.  They can be:
  //
  // 1. Logged into your app ('connected')
  // 2. Logged into Facebook, but not your app ('not_authorized')
  // 3. Not logged into Facebook and can't tell if they are logged into
  //    your app or not.
  //
  // These three cases are handled in the callback function.

  FB.getLoginStatus(function(response) {
    console.log("fbAsyncInit");
    statusChangeCallback(response);
  });

  };


  // Load the SDK asynchronously
  (function(d, s, id) {
    var js, fjs = d.getElementsByTagName(s)[0];
    if (d.getElementById(id)) return;
    js = d.createElement(s); js.id = id;
    js.src = "//connect.facebook.net/en_US/sdk.js";
    fjs.parentNode.insertBefore(js, fjs);
  }(document, 'script', 'facebook-jssdk'));


  function loginSuccess() {
    FB.api('/me', function(response) {
      console.log('Successful login for: ' + response.name);
      //document.getElementById("greeting").innerText = "Welcome, " + response.name;
      //$("#loButton").show();

      $.getJSON($SCRIPT_ROOT + '/login', {
        uid: response.id,
        name: response.name
      }, function(data) {
        console.log("RESULT: " + data);
        console.log("here: login")
        if (toReload){
          location.reload();
          toReload = false;
          }
        });
    });
  }

  function logoutSuccess() {
    //document.getElementById("loga").innerText = "Login";
    //$("#loButton").hide();
    console.log("here: logout")
    if (toReload){
      location.reload();
      toReload = false;
    }
  }

  $(document).ready(function() {
      $("#liButton").click(function() {
        toReload = true;
        FB.login(function(response) {
          console.log("LOGIN BUTTON?");
          statusChangeCallback(response);
        });
      });
      $("#loButton").click(function() {
        toReload = true;
        FB.logout(function(response) {
          console.log("LOGOUT BUTTON?")
          statusChangeCallback(response);
        });
      });
  });

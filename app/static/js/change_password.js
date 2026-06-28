// ================================
// SHOW / HIDE PASSWORD
// ================================

document.querySelectorAll(".toggle-password").forEach(function(btn){

    btn.addEventListener("click", function(){

        const input = document.getElementById(this.getAttribute("toggle"));
        const icon = this.querySelector("i");

        if(input.type === "password"){

            input.type = "text";

            icon.classList.remove("fa-eye");
            icon.classList.add("fa-eye-slash");

        }else{

            input.type = "password";

            icon.classList.remove("fa-eye-slash");
            icon.classList.add("fa-eye");

        }

    });

});


// ================================
// PASSWORD STRENGTH
// ================================

const password = document.getElementById("newPassword");

password.addEventListener("keyup", checkStrength);

function checkStrength(){

    let value = password.value;

    let score = 0;

    if(value.length >= 8)
        score++;

    if(/[A-Z]/.test(value))
        score++;

    if(/[a-z]/.test(value))
        score++;

    if(/[0-9]/.test(value))
        score++;

    if(/[!@#$%^&*(),.?":{}|<>]/.test(value))
        score++;

    const bar = document.getElementById("strengthFill");
    const text = document.getElementById("strengthText");

    switch(score){

        case 0:
        case 1:
            bar.style.width="20%";
            bar.style.background="#ff4d4f";
            text.innerHTML="Weak Password";
            break;

        case 2:
            bar.style.width="40%";
            bar.style.background="#ff9800";
            text.innerHTML="Fair Password";
            break;

        case 3:
            bar.style.width="60%";
            bar.style.background="#ffc107";
            text.innerHTML="Good Password";
            break;

        case 4:
            bar.style.width="80%";
            bar.style.background="#4caf50";
            text.innerHTML="Strong Password";
            break;

        case 5:
            bar.style.width="100%";
            bar.style.background="#2ecc71";
            text.innerHTML="Very Strong Password";
            break;
    }

}


// ================================
// PASSWORD MATCH
// ================================

const confirmPassword=document.getElementById("confirmPassword");

confirmPassword.addEventListener("keyup",function(){

    const msg=document.getElementById("matchMessage");

    if(confirmPassword.value==""){

        msg.innerHTML="";
        return;

    }

    if(password.value===confirmPassword.value){

        msg.innerHTML="✅ Password Matched";
        msg.style.color="#28a745";

    }else{

        msg.innerHTML="❌ Password Not Matched";
        msg.style.color="#dc3545";

    }

});


// ================================
// UPDATE PASSWORD
// ================================

document.getElementById("passwordForm").addEventListener("submit", async function(e){

    e.preventDefault();

    const currentPassword=document.getElementById("currentPassword").value;
    const newPassword=document.getElementById("newPassword").value;
    const confirmPassword=document.getElementById("confirmPassword").value;

    if(newPassword!==confirmPassword){

        alert("Passwords do not match.");
        return;

    }

    if(newPassword.length<8){

        alert("Password should contain minimum 8 characters.");
        return;

    }

    try{

        const response=await fetch("/change-password",{

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({

                current_password:currentPassword,
                new_password:newPassword

            })

        });

        const result=await response.json();

        if(result.success){

            alert("Password changed successfully.");

            document.getElementById("passwordForm").reset();

            document.getElementById("strengthFill").style.width="0%";

            document.getElementById("strengthText").innerHTML="Password Strength";

            document.getElementById("matchMessage").innerHTML="";

            window.location.href = "/logout";

        }else{

            alert(result.message);

        }

    }catch(err){

        console.log(err);

        alert("Server Error");

    }

});
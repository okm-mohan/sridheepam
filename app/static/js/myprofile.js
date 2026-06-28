/*=========================================
    MY PROFILE
==========================================*/

document.addEventListener("DOMContentLoaded", () => {

    const editBtn = document.getElementById("editBtn");
    const saveBtn = document.getElementById("saveBtn");

    const profileImage = document.getElementById("profilePreview");
    const photoInput = document.getElementById("photoInput");

    const editableFields = [
        "fullname",
        "mobile",
        "email",
        "dob",
        "address"
    ];

    const gender = document.getElementById("gender");

    let editMode = false;

    saveBtn.style.display = "none";

    /*==============================
        ENABLE EDIT MODE
    ==============================*/

    editBtn.addEventListener("click", () => {

        editMode = true;

        editableFields.forEach(id => {
            const field = document.getElementById(id);

            if(field){

                field.removeAttribute("readonly");
                field.style.background = "#ffffff";

            }

        });

        gender.disabled = false;

        editBtn.style.display = "none";
        saveBtn.style.display = "block";

    });

    /*==============================
        IMAGE PREVIEW
    ==============================*/

    photoInput.addEventListener("change", function(){

        const file = this.files[0];

        if(!file) return;

        if(!file.type.startsWith("image/")){

            alert("Please select an image.");

            return;

        }

        const reader = new FileReader();

        reader.onload = function(e){

            profileImage.src = e.target.result;

        };

        reader.readAsDataURL(file);

    });

    /*==============================
        SAVE
    ==============================*/

    saveBtn.addEventListener("click", () => {

        const fullname = document.getElementById("fullname").value.trim();
        const mobile = document.getElementById("mobile").value.trim();
        const email = document.getElementById("email").value.trim();

        if(fullname===""){

            alert("Full Name is required.");

            return;

        }

        if(mobile !== ""){

            const mobileRegex = /^[0-9]{10}$/;

            if(!mobileRegex.test(mobile)){

                alert("Enter valid Mobile Number.");

                return;

            }

        }

        if(email !== ""){

            const emailRegex =
            /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

            if(!emailRegex.test(email)){

                alert("Enter valid Email Address.");

                return;

            }

        }

        /*=================================
            SEND TO SERVER
        =================================*/

        /*
        const formData = new FormData();

        formData.append("fullname", fullname);
        formData.append("mobile", mobile);
        formData.append("email", email);
        formData.append("gender", gender.value);
        formData.append("dob", document.getElementById("dob").value);
        formData.append("address", document.getElementById("address").value);

        if(photoInput.files.length>0){

            formData.append("photo",photoInput.files[0]);

        }

        fetch("/api/profile/update",{

            method:"POST",

            body:formData

        })
        .then(res=>res.json())
        .then(data=>{

            if(data.success){

                alert("Profile Updated Successfully");

                location.reload();

            }
            else{

                alert(data.message);

            }

        });
        */

        alert("Profile Updated Successfully.");

        editableFields.forEach(id => {

            const field = document.getElementById(id);

            field.setAttribute("readonly", true);

            field.style.background = "#f8fafc";

        });

        gender.disabled = true;

        editBtn.style.display = "block";
        saveBtn.style.display = "none";

        editMode = false;

    });

});
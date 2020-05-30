package com.example.nutrisoft.data;
import android.content.Intent;
import com.example.nutrisoft.data.model.LoggedInUser;
import com.example.nutrisoft.menu;
import java.io.IOException;
import static androidx.core.content.ContextCompat.startActivity;

/**
 * Class that handles authentication w/ login credentials and retrieves user information.
 */
public class LoginDataSource {



    public Result<LoggedInUser> login(String username, String password) {

        try {
            // TODO: handle loggedInUser authentication
            LoggedInUser fakeUser =
                    new LoggedInUser(
                            java.util.UUID.randomUUID().toString(),
                            "Rafael");

            return new Result.Success<>(fakeUser);
        } catch (Exception e) {
            return new Result.Error(new IOException("Error logging in", e));
        }
    }

    public void logout() {
        // TODO: revoke authentication
    }
}

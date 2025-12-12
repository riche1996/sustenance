
package com.hcl.util;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

import org.apache.tomcat.util.net.jsse.JSSEImplementation;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;
import com.google.gson.JsonObject;

public class SqlliteConnection {

	private Connection connect() {

		try {
			Class.forName("org.postgresql.Driver");
		} catch (ClassNotFoundException e1) {
			e1.printStackTrace();
		}

		Connection conn = null;
		
		String host = "localhost";
		String port = "5432";
		String user = "postgres";
		String password = "Aone@1104";
		String database = "datagen";
		try {
			
			conn = DriverManager
					.getConnection("jdbc:postgresql://" + host + ":" + port + "/" + database +
							"?user=" + user
							+ "&password=" + password);

		} catch (SQLException e) {
			System.out.println(e.getMessage());
		}

		return conn;
	}

	public String createtask(String taskname) {
		String create_task_msg = "";
		try {
			Connection conn = this.connect();
			Statement statement = conn.createStatement();
			String create_sql = "CREATE TABLE IF NOT EXISTS regex_tasks (task_name VARCHAR(100), task_description TEXT,results TEXT,exec_log TEXT,"
					.concat("status VARCHAR(100),log_file_name VARCHAR(100),log_delimiter TEXT,")
					.concat("training_type VARCHAR(100),\"task_CreatedDate\" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,")
					.concat("\"task_CompletedOn\" TIMESTAMP)");
			statement.executeUpdate(create_sql);

			String select_sql = "SELECT task_name FROM regex_tasks WHERE task_name = ?";
			PreparedStatement select_pstmt = conn.prepareStatement(select_sql);
			select_pstmt.setString(1, taskname);
			ResultSet rs = select_pstmt.executeQuery();
			if (!rs.isBeforeFirst()) {
				String sql = "INSERT INTO regex_tasks(task_name,task_description,exec_log) VALUES(?,?,?)";
				PreparedStatement pstmt = conn.prepareStatement(sql);
				pstmt.setString(1, taskname);
				pstmt.setString(2, taskname);
				pstmt.setString(3, "");
				int check_insert = pstmt.executeUpdate();
				if (check_insert > 0) {
					create_task_msg = taskname + " is created successfully.";
				} else {
					create_task_msg = taskname + " is not created. Reason SQL error.";
				}
			} else {
				while (rs.next()) {
					create_task_msg = taskname + " is already available.";
				}
			}
		} catch (SQLException e) {
			
			System.err.println(e.getMessage());
		} finally {
			try {
				if (connect() != null)
					connect().close();
			} catch (SQLException e) {
				System.err.println(e);
			}
		}
		return create_task_msg;

	}

	public void updatestatus(String status, JSONObject docobj, String task_name) {
		try {
			Connection conn = this.connect();

			String sql = "UPDATE regex_tasks SET status=? where task_name=?";
			PreparedStatement pstmt = conn.prepareStatement(sql);
			pstmt.setString(1, status);
			pstmt.setString(2, task_name);
			pstmt.executeUpdate();
		} catch (SQLException e) {
	
			System.err.println(e.getMessage());
		} finally {
			try {
				if (connect() != null)
					connect().close();
			} catch (SQLException e) {
		
				System.err.println(e);
			}
		}
	}

	
	public void updateresult(JSONObject resultobj, String json) {
		System.out.println("Yes");
		System.out.println(resultobj);
		System.out.println(json);
		try {
			Connection conn = this.connect();

			String sql = "UPDATE regex_tasks SET results=?, status=? where task_name=?";
			PreparedStatement pstmt = conn.prepareStatement(sql);
			pstmt.setString(1, resultobj.toString());
			pstmt.setString(2, resultobj.getString("status"));
			pstmt.setString(3, json);
			pstmt.executeUpdate();
		} catch (SQLException e) {
			System.err.println(e.getMessage());
		} finally {
			try {
				if (connect() != null)
					connect().close();
			} catch (SQLException e) {
				System.err.println(e);
			}
		}

	}

	public String getTaskDetails(String execId) {
		String final_results = "";
		try {
			Connection conn = this.connect();
			String sql = "SELECT results from regex_tasks where task_name=?";
			PreparedStatement pstmt = conn.prepareStatement(sql);
			pstmt.setString(1, execId);
			ResultSet rs = pstmt.executeQuery();
			while (rs.next()) {
				final_results = rs.getString("results");
			}
		} catch (SQLException e) {
			final_results = "Unable to get results. Reason SQLException";
			System.err.println(e.getMessage());
		} finally {
			try {
				if (connect() != null)
					connect().close();
			} catch (SQLException e) {
				System.err.println(e);
			}
		}
		return final_results;
	}
}
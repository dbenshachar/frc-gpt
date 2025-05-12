package com.reservation.controller;

import java.io.IOException;
import java.sql.SQLException;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.sql.Date;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import com.reservation.model.ReservationModel;
import com.reservation.service.BookTicketsService;

public class BookTicketsServlet extends HttpServlet{
	

	@Override
	protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
		String source = req.getParameter("source");
		String destination = req.getParameter("destination");
		String date = req.getParameter("schedule");
		System.out.println(date);
		LocalDate date2 = LocalDate.parse(date); // Convert String to Date
		System.out.println("Converted Date: " + date2);
		int trainNumber = Integer.parseInt(req.getParameter("trainNumber"));
		int availableseats = Integer.parseInt(req.getParameter("availableSeats"));
		int numSeats = Integer.parseInt(req.getParameter("numSeats"));
		HttpSession session = req.getSession();
		long userId = (Long) session.getAttribute("userId");
		
		ReservationModel rm = new ReservationModel();
		rm.setDate(date2);
		rm.setDestination(destination);
		rm.setSource(source);
		rm.setNumSeats(numSeats);
		rm.setAvailableseats(availableseats);
		rm.setTrainNumber(trainNumber);
		
		ReservationModel result = null;
		try {
			result = BookTicketsService.bookTickets(rm, userId);
		} catch (ClassNotFoundException | SQLException e) {
			e.printStackTrace();
		}
		
		if(result == null) {
			System.out.println("NUllll in controller");
		}else {
			
			session.setAttribute("reservationId", result.getReservationId());
			session.setAttribute("trainNumber", result.getTrainNumber());
			LocalDate date0 = result.getDate();
			DateTimeFormatter formatter = DateTimeFormatter.ofPattern("dd/mm/yyyy");
			String datestr = date.formatted(formatter);
			session.setAttribute("date",datestr);
			session.setAttribute("source", result.getSource());
			session.setAttribute("destination", result.getDestination());
			session.setAttribute("seats", result.getNumSeats());
			session.setAttribute("name", result.getUserName());
			
			RequestDispatcher rd = req.getRequestDispatcher("ConfirmTickets.jsp");
			rd.forward(req, resp);
		}
	}
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.controller;

import java.sql.SQLException;

import com.reservation.repo.Login;

public class ConLogin {
	
	public static long login(String name, String password) throws SQLException {
		long userId= 0;
		try {
			userId = Login.login(name, password);
		} catch (ClassNotFoundException e) {
			e.printStackTrace();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		return userId;
	}
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.controller;

import java.io.IOException;
import java.io.PrintWriter;
import java.sql.SQLException;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

//@WebServlet("/login")
public class Login extends HttpServlet {
	{
		System.out.println("swarnarak");
	}
	@Override
	protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
		String name = req.getParameter("name");
		String password = req.getParameter("password");
//		System.out.println(name+" "+password);
		PrintWriter out = resp.getWriter();
		
		try {
			long userId = ConLogin.login(name, password);
			if(userId != 0){
			req.setAttribute("name", name);
			req.setAttribute("password", password);
			HttpSession session = req.getSession();
			session.setAttribute("userId", userId);
			System.out.println("session: "+userId);
			RequestDispatcher rd = req.getRequestDispatcher("home.jsp");
			rd.forward(req, resp);
		}else {
			RequestDispatcher rd = req.getRequestDispatcher("loginFailed.jsp");
			rd.forward(req, resp);
		}
		} catch (SQLException e) {
			e.printStackTrace();
		}
	}
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.controller;

import java.io.IOException;
import java.io.PrintWriter;
import java.sql.SQLException;
import java.sql.Timestamp;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.reservation.model.User;
import com.reservation.service.RegistrationService;

public class Registration extends HttpServlet {
	@Override
	protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
	System.out.println("controller");
	User u = new User();
	u.setUserName(req.getParameter("username"));
	u.setPassword(req.getParameter("password"));
	u.setEmail(req.getParameter("email"));
	u.setRole(req.getParameter("role"));
	Timestamp date = new Timestamp(System.currentTimeMillis());
	u.setCreatedAt(date);
	try {
		boolean result = RegistrationService.doRegister(u);
		if(result) {
			RequestDispatcher rd = req.getRequestDispatcher("index.jsp");
			rd.forward(req, resp);
		}else {
			PrintWriter out = resp.getWriter();
			out.println("failed to register");
		}
	} catch (ClassNotFoundException e) {
		e.printStackTrace();
	} catch (SQLException e) {
		e.printStackTrace();
	}
	}
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.controller;

import java.io.IOException;
import java.io.PrintWriter;
import java.time.LocalDate;
import java.util.List;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.reservation.model.Train;
import com.reservation.service.TrainDetails;

public class TrainDetailscon extends HttpServlet {
	@Override
	protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
		String source = (String) req.getParameter("source");
		String destination = (String) req.getParameter("destination");
		System.out.println(source);
		System.out.println(destination);
	
		
		resp.setContentType("text/html;charset=UTF-8");
		PrintWriter out = resp.getWriter();
		try {
			// Check if source and destination parameters are provided
			if (source == null || destination == null || source.isEmpty() || destination.isEmpty()) {
				out.println("<p>Please provide both source and destination.</p>");
				return;
			}

			List<Train> trains = TrainDetails.getDetails(source, destination);
			if (trains.isEmpty()) {
				out.println("<p>No trains available from " + source + " to " + destination + ".</p>");
			} else {
				req.setAttribute("trainList", trains);
				LocalDate currentDate = LocalDate.now();
				req.setAttribute("currentDate", currentDate);
				RequestDispatcher rd = req.getRequestDispatcher("trainList.jsp");
				rd.forward(req, resp);
			}

		} finally {
			// Close the PrintWriter
			out.close();
		}
//		out.println(source);
//		out.println(destination);
	}
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.first;

import java.io.IOException;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class LandingPage extends HttpServlet {
	@Override
	protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
		RequestDispatcher rd = req.getRequestDispatcher("login");
		rd.forward(req, resp);
	}
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.model;

import java.sql.Date;
import java.time.LocalDate;

public class ReservationModel {
	

	private String source;
	private String  destination;
	private LocalDate date;
	private int trainNumber;
	private int availableseats;
	private int numSeats;
	private String reservationId;
	private long userId;
	private String userName;
	
	public long getUserId() {
		return userId;
	}
	public void setUserId(long userId) {
		this.userId = userId;
	}
	public String getUserName() {
		return userName;
	}
	public void setUserName(String userName) {
		this.userName = userName;
	}
	public String getReservationId() {
		return reservationId;
	}
	public void setReservationId(String reservationId) {
		this.reservationId = reservationId;
	}
	
	public String getSource() {
		return source;
	}
	public void setSource(String source) {
		this.source = source;
	}
	public String getDestination() {
		return destination;
	}
	public void setDestination(String destination) {
		this.destination = destination;
	}
	public LocalDate getDate() {
		return date;
	}
	public void setDate(LocalDate date) {
		this.date = date;
	}
	public int getTrainNumber() {
		return trainNumber;
	}
	public void setTrainNumber(int trainNumber) {
		this.trainNumber = trainNumber;
	}
	public int getAvailableseats() {
		return availableseats;
	}
	public void setAvailableseats(int availableseats) {
		this.availableseats = availableseats;
	}
	public int getNumSeats() {
		return numSeats;
	}
	public void setNumSeats(int numSeats) {
		this.numSeats = numSeats;
	}
	
	public ReservationModel() {};
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.model;

import java.sql.Date;
import java.time.LocalDate;

public class Train{
	private int trainNumber;
	private String source;
	private String destination;
	private LocalDate schedule;
	private boolean isSeatsAvailable;
	private int noOfSeatsAvailable;
	private String userName;
	private long userId;
	
	public String getUserName() {
		return userName;
	}
	public void setUserName(String userName) {
		this.userName = userName;
	}
	public long getUserId() {
		return userId;
	}
	public void setUserId(long userId) {
		this.userId = userId;
	}
	public int getTrainNumber() {
		return trainNumber;
	}
	public void setTrainNumber(int trainNumber) {
		this.trainNumber = trainNumber;
	}
	public String getSource() {
		return source;
	}
	public void setSource(String source) {
		this.source = source;
	}
	public String getDestination() {
		return destination;
	}
	public void setDestination(String destination) {
		this.destination = destination;
	}
	
	public LocalDate getSchedule() {
		return schedule;
	}
	public void setSchedule(LocalDate schedule) {
		this.schedule = schedule;
	}
	public boolean isSeatsAvailable() {
		return isSeatsAvailable;
	}
	public void setSeatsAvailable(boolean isSeatsAvailable) {
		this.isSeatsAvailable = isSeatsAvailable;
	}
	public int getNoOfSeatsAvailable() {
		return noOfSeatsAvailable;
	}
	public void setNoOfSeatsAvailable(int noOfSeatsAvailable) {
		this.noOfSeatsAvailable = noOfSeatsAvailable;
	}
	@Override
	public String toString() {
		return "Train [trainNumber=" + trainNumber + ", source=" + source + ", destination=" + destination
				+ ", schedule=" + schedule + ", isSeatsAvailable=" + isSeatsAvailable + ", noOfSeatsAvailable="
				+ noOfSeatsAvailable + "]";
	}
	
	public Train() {}
	public Train(int trainNumber, String source, String destination, LocalDate schedule, boolean isSeatsAvailable,
			int noOfSeatsAvailable) {
		super();
		this.trainNumber = trainNumber;
		this.source = source;
		this.destination = destination;
		this.schedule = schedule;
		this.isSeatsAvailable = isSeatsAvailable;
		this.noOfSeatsAvailable = noOfSeatsAvailable;
	}
	
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.model;

import java.sql.Timestamp;

public class User {
	private int userId;
	private String userName;
	private String email;
	private String password;
	private String role;
	private Timestamp createdAt;
	public int getUserId() {
		return userId;
	}
	public void setUserId(int userId) {
		this.userId = userId;
	}
	public String getUserName() {
		return userName;
	}
	public void setUserName(String userName) {
		this.userName = userName;
	}
	public String getEmail() {
		return email;
	}
	public void setEmail(String email) {
		this.email = email;
	}
	public String getPassword() {
		return password;
	}
	public void setPassword(String password) {
		this.password = password;
	}
	public String getRole() {
		return role;
	}
	public void setRole(String role) {
		this.role = role;
	}

	public Timestamp getCreatedAt() {
		return createdAt;
	}
	public void setCreatedAt(Timestamp createdAt) {
		this.createdAt = createdAt;
	}

	public User(String userName, String email, String password, String role) {
		super();
		this.userName = userName;
		this.email = email;
		this.password = password;
		this.role = role;
		this.createdAt = new Timestamp(System.currentTimeMillis());
	}
	
	public User() {}
	@Override
	public String toString() {
		return "User [userId=" + userId + ", userName=" + userName + ", email=" + email + ", password=" + password
				+ ", role=" + role + ", createdAt=" + createdAt + "]";
	}

}


================================================== FILE SEPARATOR ==================================================

package com.reservation.repo;

import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import com.reservation.model.ReservationModel;
import com.reservation.service.BookTicketsService;

public class BookTicketsRepo {
	public static ReservationModel bookTickets(ReservationModel rm, long userId) throws ClassNotFoundException, SQLException {

        try (Connection con = ConnectionClass.getConnection()) {
        	System.out.println(1);
            // 1. Check availability of seats and schedule
            String checkSeatsQuery = "SELECT noOfseatedAvailable, schedule FROM train WHERE trainNumber = ?";
            try (PreparedStatement pst = con.prepareStatement(checkSeatsQuery)) {
            	System.out.println(2);
                pst.setInt(1, rm.getTrainNumber());
                ResultSet rs = pst.executeQuery();

                int availableSeats = 0;
                Date scheduleDate = null;

                if (rs.next()) {
                    availableSeats = rs.getInt("noOfseatedAvailable");
                    scheduleDate = rs.getDate("schedule");
                    System.out.println("avail: "+availableSeats);
                }
                if (availableSeats >= rm.getNumSeats()) {
                	System.out.println(4);
                	Boolean res = updateTrainSeatsAvailable(availableSeats, rm.getNumSeats(),rm);
                	System.out.println(res);
                	if(res) {
                		System.out.println(6);
                		System.out.println("update on the trainSeats");
                		String userName = getUserName(userId);
                		
                		boolean out = InsertIntoReservation(rm, userName, scheduleDate, userId);
                		System.out.println(userName+" username");
                		if(out) {
                			System.out.println("into insert");
                			String query = "select * from reservations where trainNumber = ?";
                			PreparedStatement psts = con.prepareStatement(query);
                			System.out.println(rm.getTrainNumber());
                			psts.setInt(1, rm.getTrainNumber());
                			ResultSet result = psts.executeQuery();
                			System.out.println(result);
//                			result.next();
                			if(result.next()) {
//                				rs.next();
                				System.out.println("sawa");
                				ReservationModel rem = new ReservationModel();
                				rem.setUserName(result.getString("userName"));
                				rem.setReservationId(result.getString("reservationId"));
                				rem.setSource(result.getString("source"));
                				rem.setDestination(result.getString("destination"));
                				rem.setNumSeats(result.getInt("seatNumbers"));
                				rem.setDate(result.getDate("schedule").toLocalDate());
                				rem.setTrainNumber(result.getInt("TrainNumber"));
                				System.out.println("completed insert");
                				return rem;
                			}
                		}return null;
                	}return null;
                }return null;
        }catch(SQLException e) {
        	e.printStackTrace();
        	}
        }
		return null;
	}



	public static boolean updateTrainSeatsAvailable(int available, int seatsbooked, ReservationModel rm)
			throws SQLException, ClassNotFoundException {
		System.out.println(5);
		String updateSeatsQuery = "UPDATE train SET noOfseatedAvailable = ? WHERE trainNumber = ?";
		Connection con = ConnectionClass.getConnection();
		
		PreparedStatement pst2 = con.prepareStatement(updateSeatsQuery);
			int remainingSeats = available - seatsbooked;
			pst2.setInt(1, remainingSeats);
			pst2.setInt(2, rm.getTrainNumber());
			int out = pst2.executeUpdate();
			System.out.println(out+" "+111);
		if (out>0) {
			System.out.println(out);
			return true;
		}
		return false;
	}

	public static String getUserName(long userId) throws ClassNotFoundException, SQLException {
		String userName = null;
		Connection con = ConnectionClass.getConnection();
		String getUserQuery = "SELECT userName FROM user WHERE userId = ?";
		PreparedStatement pst3 = con.prepareStatement(getUserQuery);
			pst3.setLong(1, userId);
			ResultSet userResult = pst3.executeQuery();
			if (userResult.next()) {
				userName = userResult.getString("userName");
			}return userName;
	}

	public static boolean InsertIntoReservation(ReservationModel rm, String userName, Date scheduleDate, long userId)
			throws ClassNotFoundException, SQLException {
		String insertReservationQuery = "INSERT INTO reservations "
				+ "(userId, TrainNumber, seatNumbers, status, userName, schedule, source, destination) "
				+ "VALUES (?, ?, ?, ?, ?, ?, ?, ?)";
		Connection con = ConnectionClass.getConnection();
		PreparedStatement pst4 = con.prepareStatement(insertReservationQuery);
		pst4.setLong(1, userId);
		pst4.setInt(2, rm.getTrainNumber());
		pst4.setInt(3, rm.getNumSeats());
		pst4.setBoolean(4, true); // assuming 'true' means reservation success
		pst4.setString(5, userName);
		pst4.setDate(6, scheduleDate);
		pst4.setString(7, rm.getSource());
		pst4.setString(8, rm.getDestination());

		boolean out = pst4.execute();
		if (out) {
			return true;
		}
		return true;
	}
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.repo;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class ConnectionClass {
	public static Connection getConnection() throws SQLException, ClassNotFoundException {
		Class.forName("com.mysql.cj.jdbc.Driver");
		String url = "jdbc:mysql://localhost:3306/trainreservation";
		String dbname = "root";
		String dbpass = "swarna@08";
		Connection con = DriverManager.getConnection(url, dbname, dbpass);
		return con;
	}
}	


================================================== FILE SEPARATOR ==================================================

package com.reservation.repo;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

import com.reservation.model.Train;

public class GetTrainDetails {
	public static List<Train> getTrainDetails(String source, String destination) throws SQLException, ClassNotFoundException {
		List<Train> trainDetails = new ArrayList<Train>();
		String query = "Select * from train where source = ? and destination = ?";
		Connection con = ConnectionClass.getConnection();
		PreparedStatement pst = con.prepareStatement(query);
		pst.setString(1, source);
		pst.setString(2, destination);
		ResultSet rs = pst.executeQuery();
		while(rs.next()) {
			Train a = new Train();
			a.setTrainNumber(rs.getInt("trainNumber"));
			a.setSource(rs.getString("source"));
			a.setDestination(rs.getString("destination"));
			a.setSchedule(rs.getDate("schedule").toLocalDate());
			a.setSeatsAvailable(true);
			a.setNoOfSeatsAvailable(rs.getInt("noOfseatedAvailable"));
			trainDetails.add(a);
		}
		return trainDetails;
	}
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.repo;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class Login {
	public static long login(String name, String password) throws SQLException, ClassNotFoundException {
		String getUserId = "select userId from user where userName = ?";
		Connection con = ConnectionClass.getConnection();
		PreparedStatement pst ;
		pst = con.prepareStatement(getUserId);
		pst.setString(1,name);
		ResultSet rs = pst.executeQuery();
		if(rs.next()) {
			long userId = rs.getLong("userId");
			
			String check ="select password from passwords where userId = ?";
			pst = con.prepareStatement(check);
			pst.setLong(1, userId);
			ResultSet r = pst.executeQuery();
			if(r.next()) {
				String retrivedPassword = r.getString("password");
				
				if(retrivedPassword.equals(password)) {
					return userId;
				}else{
					return 0;
				}
			}
		}
		return 0;
	}
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.repo;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

import com.reservation.model.User;

public class RegistrationRepo {
	public static boolean doRegister(User user) throws SQLException, ClassNotFoundException {
		System.out.println("repo");
		String queryInsertIntoUser = "insert into user(userName, emailId, role, createed_at) values(?, ?, ?, ?)";
		Connection con = ConnectionClass.getConnection();
		PreparedStatement pst = null;
		pst = con.prepareStatement(queryInsertIntoUser);
		System.out.println(user.getUserName());
		pst.setString(1, user.getUserName());
		pst.setString(2, user.getEmail());
		pst.setString(3, user.getRole());
		pst.setTimestamp(4, user.getCreatedAt());
//		System.out.println(user.getPassword());
		int in = pst.executeUpdate();
		System.out.println(in);
		if(in > 0) {
			String getDeatils = "select userId from user where userName = ?";
			pst = con.prepareStatement(getDeatils);
			pst.setString(1, user.getUserName());
			ResultSet r =pst.executeQuery();
			long usrID = 0;
			if(r.next()) {
				usrID = r.getLong("userId");
				System.out.println(usrID);
			}
			String insertIntoPasswords = "insert into passwords (userId, password, userName, emailId) values (?,?,?,?)";
			PreparedStatement ps ;
			 ps = con.prepareStatement(insertIntoPasswords);	         
	            ps.setLong(1, usrID);
//	            System.out.println(usrID);
//	            System.out.println(user.getPassword());
	            ps.setString(2, user.getPassword());
//	            System.out.println(user.getUserName());
	            ps.setString(3, user.getUserName());
//	            System.out.println(user.getEmail());
	            ps.setString(4, user.getEmail());
			int result = ps.executeUpdate();
			System.out.println(result);
			if(result>0) {
				return true;
			}else {
				String deleteQuery = "delete from user where userId = "+usrID;
				Statement st = con.createStatement();
				st.execute(deleteQuery);
			}
		}
		return false;
	}
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.service;

import java.sql.PreparedStatement;
import java.sql.SQLException;

import com.reservation.model.ReservationModel;
import com.reservation.repo.BookTicketsRepo;
import com.reservation.repo.ConnectionClass;

public class BookTicketsService {
	public static  ReservationModel bookTickets(ReservationModel rm, long userId) throws ClassNotFoundException, SQLException {
		ReservationModel result =  BookTicketsRepo.bookTickets(rm, userId);
		if(result == null) {
			return null;
		}return result;
	}
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.service;

import java.sql.SQLException;

import com.reservation.model.User;
import com.reservation.repo.RegistrationRepo;

public class RegistrationService {
	public static boolean doRegister(User u) throws ClassNotFoundException, SQLException {
		System.out.println("service");
		boolean result =RegistrationRepo.doRegister(u);
		return result;
	}
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.service;

public class Test {
	public static void main(String[] args) {
		
	}
}


================================================== FILE SEPARATOR ==================================================

package com.reservation.service;

import java.sql.SQLException;
import java.util.List;

import com.reservation.model.Train;
import com.reservation.repo.GetTrainDetails;

public class TrainDetails {
	public static List<Train> getDetails(String source, String destination)  {
		List<Train> trains =null;
		try {
			trains = GetTrainDetails.getTrainDetails(source, destination);
		} catch (ClassNotFoundException | SQLException e) {
			e.printStackTrace();
		}
		
		for(Train t: trains) {
			System.out.println(t);
		}
		return trains;
	}
}


================================================== FILE SEPARATOR ==================================================


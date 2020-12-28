# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.9.0 Dec 18 2020)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

from .TreePanel import TreePanel
from .LogPanel import LogPanel
import wx
import wx.xrc
import wx.propgrid as pg
import wx.aui

###########################################################################
## Class PrefsDialog
###########################################################################

class PrefsDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Preferences", pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.CAPTION|wx.RESIZE_BORDER|wx.STAY_ON_TOP )

        self.SetSizeHints( wx.Size( 400,400 ), wx.DefaultSize )

        _sizer = wx.GridBagSizer( 0, 0 )
        _sizer.SetFlexibleDirection( wx.BOTH )
        _sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self._PGM = pg.PropertyGridManager(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.propgrid.PGMAN_DEFAULT_STYLE|wx.propgrid.PG_BOLD_MODIFIED|wx.propgrid.PG_DESCRIPTION|wx.propgrid.PG_NO_INTERNAL_BORDER|wx.propgrid.PG_SPLITTER_AUTO_CENTER|wx.propgrid.PG_TOOLTIPS)
        self._PGM.SetExtraStyle( wx.propgrid.PG_EX_MODE_BUTTONS )

        self._prop_page = self._PGM.AddPage( u"Editor Preferences", wx.NullBitmap );
        _sizer.Add( self._PGM, wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 1 ), wx.EXPAND, 0 )


        _sizer.Add( ( 0, 0 ), wx.GBPosition( 1, 0 ), wx.GBSpan( 1, 1 ), wx.ALL, 5 )

        _button_sizer = wx.StdDialogButtonSizer()
        self._button_sizerSave = wx.Button( self, wx.ID_SAVE )
        _button_sizer.AddButton( self._button_sizerSave )
        self._button_sizerCancel = wx.Button( self, wx.ID_CANCEL )
        _button_sizer.AddButton( self._button_sizerCancel )
        _button_sizer.Realize();

        _sizer.Add( _button_sizer, wx.GBPosition( 2, 0 ), wx.GBSpan( 1, 1 ), wx.ALIGN_CENTER_HORIZONTAL, 0 )


        _sizer.AddGrowableCol( 0 )
        _sizer.AddGrowableRow( 0 )

        self.SetSizer( _sizer )
        self.Layout()
        _sizer.Fit( self )

        self.Centre( wx.BOTH )

        # Connect Events
        self.Bind( wx.EVT_INIT_DIALOG, self.OnInitialize )
        self._PGM.Bind( pg.EVT_PG_CHANGING, self.OnEdit )
        self._button_sizerCancel.Bind( wx.EVT_BUTTON, self.OnCancel )
        self._button_sizerSave.Bind( wx.EVT_BUTTON, self.OnCommit )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnInitialize( self, event ):
        event.Skip()

    def OnEdit( self, event ):
        event.Skip()

    def OnCancel( self, event ):
        event.Skip()

    def OnCommit( self, event ):
        event.Skip()


###########################################################################
## Class bMainFrame
###########################################################################

class bMainFrame ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"PyRRhic", pos = wx.DefaultPosition, size = wx.Size( 800,600 ), style = wx.DEFAULT_FRAME_STYLE|wx.RESIZE_BORDER|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
        self.m_mgr = wx.aui.AuiManager()
        self.m_mgr.SetManagedWindow( self )
        self.m_mgr.SetFlags(wx.aui.AUI_MGR_ALLOW_ACTIVE_PANE|wx.aui.AUI_MGR_ALLOW_FLOATING|wx.aui.AUI_MGR_LIVE_RESIZE|wx.aui.AUI_MGR_TRANSPARENT_HINT)

        self._menubar = wx.MenuBar( 0 )
        self._m_file = wx.Menu()
        self._mi_file_rom = wx.MenuItem( self._m_file, wx.ID_ANY, u"Open ROM..."+ u"\t" + u"CTRL+O", u"Open a binary ROM file", wx.ITEM_NORMAL )
        self._mi_file_rom.SetBitmap( wx.ArtProvider.GetBitmap( wx.ART_FILE_OPEN, wx.ART_MENU ) )
        self._m_file.Append( self._mi_file_rom )

        self._mi_file_prefs = wx.MenuItem( self._m_file, wx.ID_ANY, u"Preferences"+ u"\t" + u"CTRL+P", u"Open Preferences", wx.ITEM_NORMAL )
        self._mi_file_prefs.SetBitmap( wx.NullBitmap )
        self._m_file.Append( self._mi_file_prefs )

        self._menubar.Append( self._m_file, u"File" )

        self._m_view = wx.Menu()
        self._mi_view_romdata = wx.MenuItem( self._m_view, wx.ID_ANY, u"ROM Data", wx.EmptyString, wx.ITEM_CHECK )
        self._mi_view_romdata.SetBitmap( wx.ArtProvider.GetBitmap( wx.ART_TICK_MARK, wx.ART_MENU ) )
        self._m_view.Append( self._mi_view_romdata )
        self._mi_view_romdata.Check( True )

        self._mi_view_log = wx.MenuItem( self._m_view, wx.ID_ANY, u"Log", wx.EmptyString, wx.ITEM_CHECK )
        self._mi_view_log.SetBitmap( wx.ArtProvider.GetBitmap( wx.ART_TICK_MARK, wx.ART_MENU ) )
        self._m_view.Append( self._mi_view_log )
        self._mi_view_log.Check( True )

        self._menubar.Append( self._m_view, u"View" )

        self.SetMenuBar( self._menubar )

        self._status_bar = self.CreateStatusBar( 1, wx.STB_SIZEGRIP, wx.ID_ANY )
        self._tree_panel = TreePanel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_mgr.AddPane( self._tree_panel, wx.aui.AuiPaneInfo() .Name( u"RomDataPane" ).Left() .Caption( u"ROM Data" ).CloseButton( False ).PaneBorder( False ).Dock().Resizable().FloatingSize( wx.DefaultSize ).BottomDockable( False ).TopDockable( False ).MinSize( wx.Size( 400,-1 ) ) )

        self._log_panel = LogPanel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_mgr.AddPane( self._log_panel, wx.aui.AuiPaneInfo() .Name( u"LogPane" ).Center() .Caption( u"Log" ).CloseButton( False ).PaneBorder( False ).Dock().Resizable().FloatingSize( wx.Size( -1,-1 ) ).Row( 0 ).Position( 0 ) )


        self.m_mgr.Update()
        self.Centre( wx.BOTH )

        # Connect Events
        self.Bind( wx.EVT_CLOSE, self.OnClose )
        self.Bind( wx.EVT_MENU, self.OnOpenRom, id = self._mi_file_rom.GetId() )
        self.Bind( wx.EVT_MENU, self.OnPreferences, id = self._mi_file_prefs.GetId() )
        self.Bind( wx.EVT_MENU, self.OnViewRomData, id = self._mi_view_romdata.GetId() )
        self.Bind( wx.EVT_MENU, self.OnViewLog, id = self._mi_view_log.GetId() )

    def __del__( self ):
        self.m_mgr.UnInit()



    # Virtual event handlers, overide them in your derived class
    def OnClose( self, event ):
        event.Skip()

    def OnOpenRom( self, event ):
        event.Skip()

    def OnPreferences( self, event ):
        event.Skip()

    def OnViewRomData( self, event ):
        event.Skip()

    def OnViewLog( self, event ):
        event.Skip()


